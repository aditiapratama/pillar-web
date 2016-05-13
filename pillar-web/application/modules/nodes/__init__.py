import json
import logging
from datetime import datetime

from werkzeug.datastructures import MultiDict

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
from application.helpers import _get_file_cached
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


@nodes.route("/<node_id>/view")
def view(node_id):
    api = SystemUtility.attract_api()
    user_id = 'ANONYMOUS' if current_user.is_anonymous() else str(
        current_user.objectid)

    # Get node with basic embedded data
    try:
        # node = Node.find(node_id + '/?embedded={"project":1}', api=api)
        node = Node.find(node_id, api=api)
    except ResourceNotFound:
        return render_template('errors/404_embed.html')
    except ForbiddenAccess:
        return render_template('errors/403_embed.html')

    node_type_name = node.node_type

    rewrite_url = None
    embedded_node_id = None
    if request.args.get('redir') and request.args.get('redir') == '1':
        # Check the project property for the node. The only case when the prop
        # is None is if the node is a project, which usually means we are at the
        # second stage of redirection.
        if node.project:
            # Set node to embed in the session
            # session['embedded_node'] = node.to_dict()
            g.embedded_node = node.to_dict()
            # Get the project
            project = Project.find(node.project, api=api)
            # Render the project node (which will get the redir arg)
            return project_view(project.url)
        # We double check that the node is indeed of type project
        elif node_type_name == 'project':
            # Build the user name, to be used when building the full url
            if node.properties.organization:
                user = Organization.find(node.properties.organization, api=api)
                name = user.url
            else:
                name = node.user.url
            # Handle special cases (will be mainly used for items that are part
            # of the blog, or attract)
            if g.get('embedded_node')['node_type']['name'] == 'post':
                # Very special case of the post belonging to the main project,
                # which is read from the configuration.
                if node._id == app.config['MAIN_PROJECT_ID']:
                    return redirect(url_for('main_blog',
                                            url=g.get('embedded_node')[
                                                'properties']['url']))
                else:
                    return redirect(url_for('project_blog',
                                            project_url=node.properties.url,
                                            url=g.get('embedded_node')[
                                                'properties']['url']))
            rewrite_url = "/p/{0}/#{1}".format(node.properties.url,
                                               g.get('embedded_node')['_id'])
            embedded_node_id = g.get('embedded_node')['_id']

    # JsTree functionality.
    # This return a lightweight version of the node, to be used by JsTree in the
    # frontend. We have two possible cases:
    # - https://pillar/<node_id>/view?format=jstree (construct the whole
    #   expanded tree starting from the node_id. Use only once)
    # - https://pillar/<node_id>/view?format=jstree&children=1 (deliver the
    #   children of a node - use in the navigation of the tree)

    if request.args.get('format') and request.args.get('format') == 'jstree':
        if request.args.get('children') == '1':
            if node_type_name == 'storage':
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
            else:
                return jsonify(jstree_build_children(node))
        else:
            return jsonify(items=jstree_build_from_node(node))

    # Continue to process the node (for HTML, HTML embedded and JSON responses)


    def allow_link(node):
        """Helper function to cross check if the user is authenticated, and it
        is has the 'subscriber' role. Also, we check if the node has world GET
        permissions, which means it's free.
        """

        allowed_roles = ['subscriber', 'demo', 'admin']

        # Check if node permissions for the world exist (if node is free)
        if node.permissions and node.permissions.world:
            if 'GET' in node.permissions.world:
                return True
        else:
            if current_user.is_authenticated() and current_user.roles:
                for role in allowed_roles:
                    if role in current_user.roles:
                        return True
                # If no role is found, just return
                return False

            else:
                # The user is not authenticated and the node is not free
                return False

    # Set the default name of the template path based on the node name
    template_path = os.path.join('nodes', 'custom', node_type_name)
    # Set the default action for a template. By default is view and we override
    # it only if we are working storage nodes, where an 'index' is also possible
    template_action = 'view'

    # Embed the user
    if current_user.is_authenticated():
        node.user = User.find(node.user, api=api)

    # print 'Process {0}'.format(node_type_name)
    # start_t = time.time()

    # XXX Code to detect a node of type asset, and aggregate file data
    if node_type_name == 'asset':

        node_file = get_file(node.properties.file)

        # Check if the user and node status to determine if the file link should
        # be added.
        if not allow_link(node):
            node_file.link = None
        # node_file_children = node_file.children(api=api)
        # Attach the file node to the asset node
        setattr(node, 'file', node_file)

        try:
            asset_type = node_file.content_type.split('/')[0]
        except AttributeError:
            asset_type = None

        if asset_type == 'video':
            # Process video type and select video template
            sources = []
            if node_file and node_file.variations:
                for f in node_file.variations:
                    sources.append(dict(
                        type=f.content_type,
                        src=f.link))
                    # Build a link that triggers download with proper filename
                    if f.backend == 'cdnsun':
                        f.link = "{0}&name={1}.{2}".format(f.link, node.name,
                                                           f.format)
            # If the user is allowed, attach video variations to the node data
            # so that the player can function.
            if allow_link(node):
                file_variations = node_file.variations
                video_sources = json.dumps(sources)
            else:
                file_variations = video_sources = None
            setattr(node, 'video_sources', video_sources)
            setattr(node, 'file_variations', file_variations)
            template_path = os.path.join(template_path, asset_type)
        elif asset_type == 'image':
            template_path = os.path.join(template_path, asset_type)
        else:
            # Treat it as normal file (zip, blend, application, etc)
            template_path = os.path.join(template_path, 'file')
    # XXX The node is of type project
    elif node_type_name == 'project':
        if node.properties.picture_square:
            picture_square = get_file(node.properties.picture_square)
            node.properties.picture_square = picture_square
        if node.properties.picture_header:
            picture_header = get_file(node.properties.picture_header)
            node.properties.picture_header = picture_header
        if node.properties.nodes_latest:
            list_latest = []
            for node_id in node.properties.nodes_latest:
                try:
                    node_item = Node.find(node_id, {
                        'projection': '{"name":1, "user":1, "node_type":1}',
                        'embedded': '{"user":1, "node_type":1}',
                    }, api=api)
                    list_latest.append(node_item)
                except ForbiddenAccess:
                    list_latest.append(FakeNodeAsset())
            node.properties.nodes_latest = list(reversed(list_latest))
        if node.properties.nodes_featured:
            list_featured = []
            for node_id in node.properties.nodes_featured:
                try:
                    node_item = Node.find_one({
                        'where': '{"_id": "%s"}' % node_id,
                        'projection': '{"name":1, "user":1, "picture":1, "node_type":1}',
                        'embedded': '{"user":1, "node_type":1}',
                    }, api=api)
                    if node_item.picture:
                        picture = get_file(node_item.picture)
                        node_item.picture = picture
                    list_featured.append(node_item)
                except ForbiddenAccess:
                    list_featured.append(FakeNodeAsset())
            node.properties.nodes_featured = list(reversed(list_featured))
        if node.properties.nodes_blog:
            list_blog = []
            for node_id in node.properties.nodes_blog:
                try:
                    node_item = Node.find(node_id, {
                        'projection': '{"name":1, "user":1, "node_type":1}',
                        'embedded': '{"user":1, "node_type":1}',
                    }, api=api)
                    list_blog.append(node_item)
                except ForbiddenAccess:
                    list_blog.append(FakeNodeAsset())
            node.properties.nodes_blog = list(reversed(list_blog))

    elif node_type_name == 'storage':
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

    elif node_type_name == 'texture':
        for f in node.properties.files:
            f.file = get_file(f.file)
            if not allow_link(node):
                f.file.link = None

    # Get previews
    node.picture = get_file(node.picture) if node.picture else None
    # Get Parent
    try:
        parent = Node.find(node['parent'], api=api)
    except KeyError:
        parent = None
    except ResourceNotFound:
        parent = None
    # Get children
    try:
        if node_type_name == 'group':
            published_status = ',"properties.status": "published"'
            node_type_projection = ', "permissions.world": 1'
        else:
            published_status = ''
            node_type_projection = ', "properties.files": 1, "properties.is_tileable": 1'

        children = Node.all({
            'projection': '{"project":1, "name": 1, "picture": 1, "parent": 1, \
                "node_type": 1, "properties.order": 1, "properties.status": 1, \
                "user": 1, \
                "properties.content_type": 1 %s}' % (node_type_projection),
            'where': '{"parent": "%s" %s}' % (node._id, published_status),
            'sort': 'properties.order'}, api=api)
        children = children._items

    except ForbiddenAccess:
        return render_template('errors/403.html')
    for child in children:
        child.picture = get_file(child.picture) if child.picture else None

    if request.args.get('format'):
        if request.args.get('format') == 'json':
            node = node.to_dict()
            node['url_edit'] = url_for('nodes.edit', node_id=node['_id']),
            if parent:
                parent = parent.to_dict()
            return_content = jsonify({
                'node': node,
                'children': children.to_dict(),
                'parent': parent
            })
    else:
        embed_string = ''
        # Check if we want to embed the content via an AJAX call
        if request.args.get('embed'):
            if request.args.get('embed') == '1':
                # Define the prefix for the embedded template
                embed_string = '_embed'

        # Check if template exists on the filesystem
        template_path = '{0}/{1}{2}.html'.format(template_path,
                                                 template_action, embed_string)
        template_path_full = os.path.join(app.config['TEMPLATES_PATH'],
                                          template_path)
        if not os.path.exists(template_path_full):
            return "Missing template '{0}'".format(template_path)

        return_content = render_template(template_path,
                                         node_id=node._id,
                                         user_string_id=user_id,
                                         node=node,
                                         rewrite_url=rewrite_url,
                                         embedded_node_id=embedded_node_id,
                                         parent=parent,
                                         children=children,
                                         config=app.config,
                                         api=api)

    return return_content


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
                log.warning('%s not found in form for node %s', prop_name, node_id)
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
                    # Extra entries are caused by min_entries=1 in the form creation.
                    field_list = form[prop_name]
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
                if prop_name == 'files' and not db_prop_value:
                    schema = schema_prop['schema']['schema']
                    for _ in db_prop_value:
                        file_form_class = build_file_select_form(schema)
                        subform = file_form_class()
                        form[prop_name].append_entry(subform)

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
        if process_node_form(form, node_id=node_id, node_type=node_type,
                             user=user_id):
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
            error = "Server error"
            print ("Error sending data")
    else:
        if form.errors:
            print form.errors

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


# Import of custom modules (using the same nodes decorator)
from application.modules.nodes.custom.assets import *
from application.modules.nodes.custom.groups import *
