import json
import logging
from datetime import datetime

from werkzeug.datastructures import MultiDict

import pillarsdk
from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk import User
from pillarsdk import Organization
from pillarsdk import Project
from pillarsdk.exceptions import ResourceNotFound
from pillarsdk.exceptions import ForbiddenAccess

from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import jsonify
from flask import abort
from flask import g
from werkzeug.exceptions import NotFound
from wtforms import SelectMultipleField, FieldList
from flask.ext.login import login_required
from jinja2.exceptions import TemplateNotFound

from application import app
from application import cache
from application.modules.nodes.forms import get_node_form
from application.modules.nodes.forms import process_node_form
from application.modules.nodes.custom.storage import StorageNode
from application.modules.projects import view as project_view
from application.modules.projects import project_update_nodes_list
from application.helpers import get_file
from application.helpers.caching import delete_redis_cache_template
from application.helpers.jstree import jstree_build_children
from application.helpers.jstree import jstree_build_from_node
from application.helpers.forms import ProceduralFileSelectForm, build_file_select_form, \
    CustomFormField

nodes = Blueprint('nodes', __name__)
log = logging.getLogger(__name__)


class FakeUser(object):
    def __init__(self):
        super(FakeUser, self).__init__()
        self.full_name = 'Anonymous user'


class FakeNodeAsset(Node):
    def __init__(self):
        super(FakeNodeAsset, self).__init__()
        self.name = 'Asset'
        self.description = 'Login to view this asset'
        self.user = FakeUser()
        self.properties = None


@cache.memoize(timeout=3600 * 23)
def get_node(node_id, user_id):
    api = SystemUtility.attract_api()
    node = Node.find(node_id + '/?embedded={"node_type":1}', api=api)
    return node.to_dict()


@cache.memoize(timeout=3600 * 23)
def get_node_children(node_id, node_type_name, user_id):
    """This function is currently unused since it does not give significant
    performance improvements.
    """
    api = SystemUtility.attract_api()
    if node_type_name == 'group':
        published_status = ',"properties.status": "published"'
    else:
        published_status = ''

    children = Node.all({
        'where': '{"parent": "%s" %s}' % (node_id, published_status),
        'embedded': '{"node_type": 1}'}, api=api)
    return children.to_dict()


@nodes.route("/<node_id>/jstree")
def jstree(node_id):
    """JsTree view.

    This return a lightweight version of the node, to be used by JsTree in the
    frontend. We have two possible cases:
    - https://pillar/<node_id>/jstree (construct the whole
      expanded tree starting from the node_id. Use only once)
    - https://pillar/<node_id>/jstree&children=1 (deliver the
      children of a node - use in the navigation of the tree)
    """

    # Get node with basic embedded data
    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)

    if request.args.get('children') != '1':
        return jsonify(items=jstree_build_from_node(node))

    if node.node_type == 'storage':
        storage = StorageNode(node)
        # Check if we specify a path within the storage
        path = request.args.get('path')
        # Generate the storage listing
        listing = storage.browse(path)
        # Inject the current node id in the response, so that JsTree can
        # expose the storage_node property and use it for further queries
        listing['storage_node'] = node._id
        if 'children' in listing:
            for child in listing['children']:
                child['storage_node'] = node._id
        return jsonify(listing)

    return jsonify(jstree_build_children(node))


@nodes.route("/<node_id>/view")
def view(node_id):
    api = SystemUtility.attract_api()

    # Get node with basic embedded data
    # FIXME: it looks like the links on 'picture' aren't refreshed when it's fetched
    # as embedded document.
    try:
        node = Node.find(node_id, api=api)
    except ResourceNotFound:
        return render_template('errors/404_embed.html')
    except ForbiddenAccess:
        return render_template('errors/403_embed.html')

    node_type_name = node.node_type

    if node_type_name == 'post':
        # Posts shouldn't be shown using this end point, redirect to the correct one.
        return redirect(url_for_node(node=node))

    # Set the default name of the template path based on the node name
    template_path = os.path.join('nodes', 'custom', node_type_name)
    # Set the default action for a template. By default is view and we override
    # it only if we are working storage nodes, where an 'index' is also possible
    template_action = 'view'

    node_type_handlers = {
        'asset': _view_handler_asset,
        'storage': _view_handler_storage,
        'texture': _view_handler_texture,
    }
    if node_type_name in node_type_handlers:
        handler = node_type_handlers[node_type_name]
        template_path, template_action = handler(node, template_path, template_action)

    # Fetch linked resources.
    node.picture = get_file(node.picture)
    node.user = node.user and pillarsdk.User.find(node.user, api=api)
    node.parent = node.parent and pillarsdk.Node.find(node.parent, api=api)

    # Get children
    children_projection = {'project': 1, 'name': 1, 'picture': 1, 'parent': 1,
                           'node_type': 1, 'properties.order': 1, 'properties.status': 1,
                           'user': 1, 'properties.content_type': 1}
    children_where = {'parent': node._id}

    if node_type_name == 'group':
        children_where['properties.status'] = 'published'
        children_projection['permissions.world'] = 1
    else:
        children_projection['properties.files'] = 1
        children_projection['properties.is_tileable'] = 1

    try:
        children = Node.all({
            'projection': children_projection,
            'where': children_where,
            'sort': [('properties.order', 1), ('name', 1)]}, api=api)
    except ForbiddenAccess:
        return render_template('errors/403_embed.html')
    children = children._items

    for child in children:
        child.picture = get_file(child.picture)

    if request.args.get('format') == 'json':
        node = node.to_dict()
        node['url_edit'] = url_for('nodes.edit', node_id=node['_id']),
        return jsonify({
            'node': node,
            'children': children.to_dict(),
            'parent': node.parent.to_dict() if node.parent else {}
        })

    # Check if template exists on the filesystem
    template_path = '{0}/{1}_embed.html'.format(template_path, template_action)
    template_path_full = os.path.join(app.config['TEMPLATES_PATH'], template_path)

    if not os.path.exists(template_path_full):
        raise NotFound("Missing template '{0}'".format(template_path))

    return render_template(template_path,
                           node_id=node._id,
                           node=node,
                           parent=node.parent,
                           children=children,
                           config=app.config,
                           api=api)


def _view_handler_asset(node, template_path, template_action):
    # Attach the file document to the asset node
    node_file = get_file(node.properties.file)
    node.file = node_file

    if node_file and node_file.content_type is not None:
        asset_type = node_file.content_type.split('/')[0]
    else:
        asset_type = None

    if asset_type == 'video':
        # Process video type and select video template
        sources = []
        if node_file and node_file.variations:
            for f in node_file.variations:
                sources.append({'type': f.content_type, 'src': f.link})
                # Build a link that triggers download with proper filename
                # TODO: move this to Pillar
                if f.backend == 'cdnsun':
                    f.link = "{0}&name={1}.{2}".format(f.link, node.name, f.format)
        node.video_sources = json.dumps(sources)
        node.file_variations = node_file.variations
    elif asset_type != 'image':
        # Treat it as normal file (zip, blend, application, etc)
        asset_type = 'file'

    template_path = os.path.join(template_path, asset_type)

    return template_path, template_action


def _view_handler_storage(node, template_path, template_action):
    storage = StorageNode(node)
    path = request.args.get('path')
    listing = storage.browse(path)
    node.name = listing['name']
    listing['storage_node'] = node._id
    # If the item has children we are working with a group
    if 'children' in listing:
        for child in listing['children']:
            child['storage_node'] = node._id
            child['name'] = child['text']
            child['content_type'] = os.path.dirname(child['type'])
        node.children = listing['children']
        template_action = 'index'
    else:
        node.status = 'published'
        node.length = listing['size']
        node.download_link = listing['signed_url']
    return template_path, template_action


def _view_handler_texture(node, template_path, template_action):
    for f in node.properties.files:
        f.file = get_file(f.file)

    return template_path, template_action


@nodes.route("/<node_id>/edit", methods=['GET', 'POST'])
@login_required
def edit(node_id):
    """Generic node editing form
    """

    def set_properties(dyn_schema, form_schema, node_properties, form,
                       prefix="",
                       set_data=True):
        """Initialize custom properties for the form. We run this function once
        before validating the function with set_data=False, so that we can set
        any multiselect field that was originally specified empty and fill it
        with the current choices.
        """
        for prop in dyn_schema:
            schema_prop = dyn_schema[prop]
            form_prop = form_schema[prop]
            prop_name = "{0}{1}".format(prefix, prop)

            if schema_prop['type'] == 'dict':
                set_properties(
                    schema_prop['schema'],
                    form_prop['schema'],
                    node_properties[prop_name],
                    form,
                    "{0}__".format(prop_name))
                continue

            if prop_name not in form:
                continue

            try:
                db_prop_value = node_properties[prop]
            except KeyError:
                log.debug('%s not found in form for node %s', prop_name, node_id)
                continue

            if schema_prop['type'] == 'datetime':
                db_prop_value = datetime.strptime(db_prop_value,
                                                  app.config['RFC1123_DATE_FORMAT'])

            if isinstance(form[prop_name], SelectMultipleField):
                # If we are dealing with a multiselect field, check if
                # it's empty (usually because we can't query the whole
                # database to pick all the choices). If it's empty we
                # populate the choices with the actual data.
                if not form[prop_name].choices:
                    form[prop_name].choices = [(d, d) for d in db_prop_value]
                    # Choices should be a tuple with value and name

            # Assign data to the field
            if set_data:
                if prop_name == 'attachments':
                    for attachment_collection in db_prop_value:
                        for a in attachment_collection['files']:
                            attachment_form = ProceduralFileSelectForm()
                            attachment_form.file = a['file']
                            attachment_form.slug = a['slug']
                            attachment_form.size = 'm'
                            form[prop_name].append_entry(attachment_form)

                elif prop_name == 'files':
                    schema = schema_prop['schema']['schema']
                    # Extra entries are caused by min_entries=1 in the form
                    # creation.
                    field_list = form[prop_name]
                    if len(db_prop_value) > 0:
                        while len(field_list):
                            field_list.pop_entry()

                    for file_data in db_prop_value:
                        file_form_class = build_file_select_form(schema)
                        subform = file_form_class()
                        for key, value in file_data.iteritems():
                            setattr(subform, key, value)
                        field_list.append_entry(subform)

                # elif prop_name == 'tags':
                #     form[prop_name].data = ', '.join(data)
                else:
                    form[prop_name].data = db_prop_value
            else:
                # Default population of multiple file form list (only if
                # we are getting the form)
                if request.method == 'POST':
                    continue
                if prop_name == 'attachments':
                    if not db_prop_value:
                        attachment_form = ProceduralFileSelectForm()
                        attachment_form.file = 'file'
                        attachment_form.slug = ''
                        attachment_form.size = ''
                        form[prop_name].append_entry(attachment_form)

    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)
    project = Project.find(node.project, api=api)
    node_type = project.get_node_type(node.node_type)
    form = get_node_form(node_type)
    user_id = current_user.objectid
    dyn_schema = node_type['dyn_schema'].to_dict()
    form_schema = node_type['form_schema'].to_dict()
    error = ""

    node_properties = node.properties.to_dict()

    ensure_lists_exist_as_empty(node.to_dict(), node_type)
    set_properties(dyn_schema, form_schema, node_properties, form,
                   set_data=False)

    if form.validate_on_submit():
        if process_node_form(form, node_id=node_id, node_type=node_type, user=user_id):
            # Handle the specific case of a blog post
            if node_type.name == 'post':
                project_update_nodes_list(node, list_name='blog')
            else:
                project_update_nodes_list(node)
            # Emergency hardcore cache flush
            # cache.clear()
            return redirect(url_for('nodes.view', node_id=node_id, embed=1,
                                    _external=True,
                                    _scheme=app.config['SCHEME']))
        else:
            log.debug('Error sending data to Pillar, see Pillar logs.')
            error = 'Server error'
    else:
        if form.errors:
            log.debug('Form errors: %s', form.errors)

    # Populate Form
    form.name.data = node.name
    form.description.data = node.description
    if 'picture' in form:
        form.picture.data = node.picture
    if node.parent:
        form.parent.data = node.parent

    set_properties(dyn_schema, form_schema, node_properties, form)

    # Get previews
    node.picture = get_file(node.picture) if node.picture else None

    # Get Parent
    try:
        parent = Node.find(node['parent'], api=api)
    except KeyError:
        parent = None
    except ResourceNotFound:
        parent = None

    embed_string = ''
    # Check if we want to embed the content via an AJAX call
    if request.args.get('embed'):
        if request.args.get('embed') == '1':
            # Define the prefix for the embedded template
            embed_string = '_embed'

    template = '{0}/edit{1}.html'.format(node_type['name'], embed_string)

    # We should more simply check if the template file actually exsists on
    # the filesystem level
    try:
        return render_template(
            template,
            node=node,
            parent=parent,
            form=form,
            errors=form.errors,
            error=error,
            api=api)
    except TemplateNotFound:
        template = 'nodes/edit{1}.html'.format(node_type['name'], embed_string)
        return render_template(
            template,
            node=node,
            parent=parent,
            form=form,
            errors=form.errors,
            error=error,
            api=api)


@nodes.route("/<node_id>/delete", methods=['GET', 'POST'])
@login_required
def delete(node_id):
    """Generic node deletion
    """
    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)
    name = node.name
    node_type = NodeType.find(node.node_type, api=api)
    try:
        node.delete(api=api)
        forbidden = False
    except ForbiddenAccess:
        forbidden = True

    if not forbidden:
        # print (node_type['name'])
        return redirect(
            url_for('nodes.index', node_type_name=node_type['name']))
    else:
        return redirect(url_for('nodes.edit', node_id=node._id))


def ensure_lists_exist_as_empty(node_doc, node_type):
    """Ensures that any properties of type 'list' exist as empty lists.

    This allows us to iterate over lists without worrying that they
    are set to None. Only works for top-level list properties.
    """

    node_properties = node_doc.setdefault('properties', {})

    for prop, schema in node_type.dyn_schema.to_dict().iteritems():
        if schema['type'] != 'list':
            continue

        if node_properties.get(prop) is None:
            node_properties[prop] = []


@nodes.route('/create', methods=['POST'])
@login_required
def create():
    """Create a node. Requires a number of params:

    - project id
    - node_type
    - parent node (optional)
    """
    if request.method != 'POST':
        return abort(403)

    project_id = request.form['project_id']
    parent_id = request.form.get('parent_id')
    node_type_name = request.form['node_type_name']

    api = SystemUtility.attract_api()
    # Fetch the Project or 404
    try:
        project = Project.find(project_id, api=api)
    except ResourceNotFound:
        return abort(404)

    node_type = project.get_node_type(node_type_name)
    node_type_name = 'folder' if node_type['name'] == 'group' else \
        node_type['name']

    node_props = dict(
        name='New {}'.format(node_type_name),
        project=project['_id'],
        user=current_user.objectid,
        node_type=node_type['name'],
        properties={}
    )

    if parent_id:
        node_props['parent'] = parent_id

    ensure_lists_exist_as_empty(node_props, node_type)

    node = Node(node_props)
    node.create(api=api)

    return jsonify(status='success', data=dict(asset_id=node['_id']))


@app.route('/search')
def nodes_search_index():
    return render_template('nodes/search.html')


@nodes.route("/<node_id>/redir")
def redirect_to_context(node_id):
    """Redirects to the context URL of the node.

    Comment: redirects to whatever the comment is attached to + #node_id
        (unless 'whatever the comment is attached to' already contains '#', then
         '#node_id' isn't appended)
    Post: redirects to main or project-specific blog post
    Other: redirects to project.url + #node_id
    """

    url = url_for_node(node_id)
    return redirect(url)


def url_for_node(node_id=None, node=None):
    assert isinstance(node_id, (basestring, type(None)))
    # assert isinstance(node, (Node, type(None))), 'wrong type for node: %r' % type(node)

    api = SystemUtility.attract_api()

    # Find node by its ID, or the ID by the node, depending on what was passed as parameters.
    if node is None:
        try:
            node = Node.find(node_id, api=api)
        except ResourceNotFound:
            log.warning('url_for_node(node_id=%r, node=None): Unable to find node.', node_id)
            raise ValueError('Unable to find node %r' % node_id)
    elif node_id is None:
        node_id = node['_id']
    else:
        raise ValueError('Either node or node_id must be given')

    # Find the node's project, or its ID, depending on whether a project was embedded.
    # This is needed in two of the three finder functions.
    project_id = node.project
    if isinstance(project_id, pillarsdk.Resource):
        # Embedded project
        project = project_id
        project_id = project['_id']
    else:
        project = None

    def project_or_error():
        """Returns the project, raising a ValueError if it can't be found."""

        if project is not None:
            return project

        try:
            return Project.find(project_id, {'projection': {'url': 1}}, api=api)
        except ResourceNotFound:
            log.warning('url_for_node(node_id=%r): Unable to find project %r',
                        node_id, project_id)
            raise ValueError('Unable to find node project %r' % project_id)

    def find_for_comment():
        """Returns the URL for a comment."""

        parent = node
        while parent.node_type == 'comment':
            if isinstance(parent.parent, pillarsdk.Resource):
                parent = parent.parent
                continue

            try:
                parent = Node.find(parent.parent, api=api)
            except ResourceNotFound:
                log.warning('url_for_node(node_id=%r): Unable to find parent node %r',
                            node_id, parent.parent)
                raise ValueError('Unable to find parent node %r' % parent.parent)

        # Find the redirection URL for the parent node.
        parent_url = url_for_node(node=parent)
        if '#' in parent_url:
            # We can't attach yet another fragment, so just don't link to the comment for now.
            return parent_url
        return parent_url + '#{}'.format(node_id)

    def find_for_post():
        """Returns the URL for a blog post."""

        if str(project_id) == app.config['MAIN_PROJECT_ID']:
            return url_for('main_blog',
                           url=node.properties.url)

        return url_for('project_blog',
                       project_url=project_or_error().url,
                       url=node.properties.url)

    # Fallback: Assets, textures, and other node types.
    def find_for_other():
        return url_for('projects.view',
                       project_url=project_or_error().url) + '#{}'.format(node_id)

    # Determine which function to use to find the correct URL.
    url_finders = {
        'comment': find_for_comment,
        'post': find_for_post,
    }

    finder = url_finders.get(node.node_type, find_for_other)
    return finder()


# Import of custom modules (using the same nodes decorator)
from application.modules.nodes.custom.assets import *
from application.modules.nodes.custom.groups import *
