import json
import os
from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk import User
from pillarsdk import File
# from pillarsdk import binaryFile
from pillarsdk.exceptions import ResourceNotFound
from pillarsdk.exceptions import ForbiddenAccess

from flask import abort
from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import flash
from flask import url_for
from flask import request
from flask import jsonify

from datetime import datetime

from application.modules.nodes.forms import get_node_form
from application.modules.nodes.forms import get_comment_form
from application.modules.nodes.forms import process_node_form
from application.helpers import Pagination

from application import app
from application import SystemUtility

from flask.ext.login import login_required
from flask.ext.login import current_user

from jinja2.exceptions import TemplateNotFound

RFC1123_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

nodes = Blueprint('nodes', __name__)

def type_names():
    api = SystemUtility.attract_api()

    types = NodeType.all(api=api)['_items']
    type_names = []
    for names in types:
        type_names.append(str(names['name']))
    return type_names

def assigned_users_to(node, node_type):
    api = SystemUtility.attract_api()

    if node_type['name'] != "task":
        return []
    users = node['properties']['owners']['users']
    owners = []
    for user in users:
        user_node = User.find(user, api=api)
        owners.append(user_node)
    return owners

@nodes.route("/<node_type_name>")
@login_required
def index(node_type_name=""):
    """Generic function to list all nodes
    """
    # Pagination index
    page = request.args.get('page', 1)
    max_results = 50

    api = SystemUtility.attract_api()
    if node_type_name == "":
        node_type_name = "shot"

    node_type = NodeType.find_first({
        'where': '{"name" : "%s"}' % node_type_name,
        }, api=api)

    if not node_type:
        return "Empty NodeType list", 200

    nodes = Node.all({
        'where': '{"node_type" : "%s"}' % (node_type._id),
        'max_results': max_results,
        'page': page,
        'embedded': '{"picture":1}',
        'sort' : "order"}, api=api)

    # Build the pagination object
    pagination = Pagination(int(page), max_results, nodes._meta.total)

    template = '{0}/index.html'.format(node_type_name)
    try:
        return render_template(
            template,
            title=node_type_name,
            nodes=nodes,
            node_type=node_type,
            type_names=type_names(),
            pagination=pagination)
    except TemplateNotFound:
        return render_template(
            'nodes/index.html',
            title=node_type_name,
            nodes=nodes,
            node_type=node_type,
            type_names=type_names(),
            pagination=pagination)


@nodes.route("/<node_type_id>/add", methods=['GET', 'POST'])
@login_required
def add(node_type_id):
    """Generic function to add a node of any type
    """
    api = SystemUtility.attract_api()
    ntype = NodeType.find(node_type_id, api=api)
    form = get_node_form(ntype)
    user_id = current_user.objectid
    if form.validate_on_submit():
        if process_node_form(form, node_type=ntype, user=user_id):
            flash('Node correctly added')
            return redirect(url_for('nodes.index', node_type_name=ntype['name']))
    else:
        print form.errors
    return render_template('nodes/add.html',
        node_type=ntype,
        form=form,
        errors=form.errors,
        type_names=type_names())


def jstree_parse_node(node, children=None):
    """Generate JStree node from node object"""
    n = {'id': node._id, 'text': node.name, 'type': node.node_type.name, 'children': True}
    # if children:
    #     n['children'] = children
    return n


def jstree_get_children(node_id):
    api = SystemUtility.attract_api()
    children = Node.all({
        'projection': '{"name":1, "parent":1, "node_type": 1}',
        'embedded': '{"node_type":1}',
        'where': '{"parent": "%s"}' % node_id}, api=api)

    children_list = []
    for child in children._items:
        children_list.append(jstree_parse_node(child))
    return children_list


def jstree_build_children(node):
    return dict(
        id=node['_id'],
        text=node['name'],
        type='group',
        children=jstree_get_children(node['_id'])
    )

def jstree_build_from_node(node):
    api = SystemUtility.attract_api()
    open_nodes = [jstree_parse_node(node)]
    # Get the current node again (with parent data)
    #parent = Node.find(node.parent + '/?projection={"name":1, "parent":1, "node_type.name": 1}&embedded={"node_type":1}', api=api)
    try:
        parent = Node.find(node.parent, {
            'projection': '{"name":1, "parent":1, "node_type": 1}',
            'embedded': '{"node_type":1}',
            }, api=api)
    except ResourceNotFound:
        parent = None
    while (parent):
        open_nodes.append(jstree_parse_node(parent))
        # If we have a parent
        if parent.parent:
            try:
                parent = Node.find(parent.parent, {
                    'projection': '{"name":1, "parent":1, "node_type": 1}',
                    'embedded': '{"node_type":1}',
                    }, api=api)
            except ResourceNotFound:
                parent = None
        else:
            parent = None
    open_nodes.reverse()
    #open_nodes.pop(0)

    nodes_list = []

    for node in jstree_get_children(open_nodes[0]['id']):
        # Nodes at the root of the project
        node_dict = {
            'id': node['id'],
            'text': node['text'],
            'type': 'chapter',
            'children': True
        }
        if len(open_nodes) > 1:
            # Opening and selecting the tree nodes according to the landing place
            if node['id'] == open_nodes[1]['id']:
                current_dict = node_dict
                current_dict['state'] = {'opened': True}
                current_dict['children'] = jstree_get_children(node['id'])
                # Iterate on open_nodes until the end
                for n in open_nodes[2:]:
                    for c in current_dict['children']:
                        if n['id'] == c['id']:
                            current_dict = c
                            break
                    current_dict['state'] = {'opened': True}
                    current_dict['children'] = jstree_get_children(n['id'])

                # if landing_asset_id:
                #     current_dict['children'] = aux_product_tree_node(open_nodes[-1])
                #     for asset in current_dict['children']:
                #         if int(asset['id'][1:])==landing_asset_id:
                #             asset.update(state=dict(selected=True))

        nodes_list.append(node_dict)
    return nodes_list


@nodes.route("/<node_id>/view")
@login_required
def view(node_id):
    api = SystemUtility.attract_api()
    # Get node with embedded picture data
    try:
        node = Node.find(node_id + '/?embedded={"picture":1, "node_type":1}', api=api)
    except ResourceNotFound:
        return abort(404)

    # JsTree functionality.
    # This return a lightweight version of the node, to be used by JsTree in the
    # frontend. We have two possible cases:
    # - https://pillar/<node_id>/view?format=jstree (construct the whole expanded
    #   tree starting from the node_id. Use only once)
    # - https://pillar/<node_id>/view?format=jstree&children=1 (deliver the
    #   children of a node - use in the navigation of the tree)

    if request.args.get('format') and request.args.get('format') == 'jstree':
        if request.args.get('children') == '1':
            return jsonify(jstree_build_children(node))
        else:
            return jsonify(items=jstree_build_from_node(node))

    # Continue to process the node (for HTML, HTML embeded and JSON responses)

    # Get node type
    node_type = node.node_type #NodeType.find(node['node_type'], api=api)
    template_path = node_type['name']

    # XXX Code to detect a node of type asset, and aggregate file data
    if node.node_type.name == 'asset':
        node_file = File.find(node.properties.file, api=api)
        node_file_children = node_file.children(api=api)
        # Attach the file node to the asset node
        setattr(node, 'file', node_file)

        try:
            asset_type = node_file.content_type.split('/')[0]
        except AttributeError:
            asset_type = None

        if asset_type == 'video':
            # Process video type and select video template
            sources = []
            if node_file_children:
                for f in node_file_children._items:
                    sources.append(dict(
                        type=f.content_type,
                        src=f.link))

            setattr(node, 'video_sources', json.dumps(sources))
            setattr(node, 'file_children', node_file_children)
            template_path = os.path.join(template_path, asset_type)
        elif asset_type == 'image':
            # Process image type and select image template
            #setattr(node, 'file_children', node_file_children)
            template_path = os.path.join(template_path, asset_type)
        else:
            # Treat it as normal file (zip, blend, application, etc)
            template_path = os.path.join(template_path, 'file')


    user_id = current_user.objectid

    # Get comment type
    comment_type = NodeType.find_first({'where': '{"name" : "comment"}'}, api=api)
    # comment_type = comment_type['_items'][0]

    # Get comments form
    comment_form = get_comment_form(node, comment_type)
    if comment_form.validate_on_submit():
        if process_node_form(comment_form,
                                node_id=None,
                                node_type=comment_type,
                                user=user_id):
            node = Node.find(node_id + '/?embedded={"picture":1}', api=api)
        else:
            if comment_form.errors:
                print(comment_form.errors)
    # Get previews
    if node.picture:
        # picture_node = File.find(node.picture._id + \
        #                         '/?embedded={"previews":1}', api=api)
        picture_node = File.find(node.picture._id, api=api)
        picture_node_thumbnail_s = picture_node.thumbnail('s', api=api)
        if picture_node_thumbnail_s:
            node.picture = picture_node_thumbnail_s.link
        else:
            node.picture = picture_node.link
        #node['picture'] = "{0}{1}".format(SystemUtility.attract_server_endpoint_static(), picture_node.path)
        # if picture_node.previews:
        #     for preview in picture_node.previews:
        #         if preview.size == 'l':
        #             node['picture_thumbnail'] = "{0}{1}".format(SystemUtility.attract_server_endpoint_static(), preview.path)
        #             break
        # else:
        #     node['picture_thumbnail'] = node['picture']
    # Get Parent
    try:
        parent = Node.find(node['parent'], api=api)
    except KeyError:
        parent = None
    except ResourceNotFound:
        parent = None
    # Get children
    children = Node.all({
        'where': '{"parent": "%s"}' % node._id,
        'embedded': '{"picture": 1, "user": 1}'}, api=api)

    children = children.to_dict()['_items']
    # TODO this logic should be on Server:
    AllNodeTypes = NodeType.all(api=api)
    for child in children:
        for ntype in AllNodeTypes['_items']:
            if child['node_type'] == ntype['_id']:
                child['node_type_name'] = ntype['name']
                break
    # Get Comments
    comments = []
    for child in children:
        if child['node_type'] == comment_type['_id']:
            comments.append(child)

    # Get comment attachments
    for comment in comments:
        comment['attachments'] = []
        for attachment in comment['properties']['attachments']:
            try:
                attachment_file = File.find(attachment, api=api)
            except ResourceNotFound:
                attachment_file = None
            comment['attachments'].append(attachment_file)

    # Get assigned users
    assigned_users = assigned_users_to(node, node_type)

    if request.args.get('format'):
        if request.args.get('format') == 'json':
            node = node.to_dict()
            node['url_edit'] = url_for('nodes.edit', node_id=node['_id']),
            if parent:
                parent = parent.to_dict()
            return_content = jsonify({
                'node': node,
                'children': children,
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
        template_path = '{0}/view{1}.html'.format(template_path, embed_string)
        template_path_full = os.path.join(app.config['TEMPLATES_PATH'], template_path)
        if not os.path.exists(template_path_full):
            template_path = 'nodes/view.html'

        return_content = render_template(template_path,
            node=node,
            type_names=type_names(),
            parent=parent,
            children=children,
            comments=comments,
            comment_form=comment_form,
            assigned_users=assigned_users,
            config=app.config)


    return return_content



@nodes.route("/<node_id>/edit", methods=['GET', 'POST'])
@login_required
def edit(node_id):
    """Generic node editing form
    """
    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)
    node_type = NodeType.find(node.node_type, api=api)
    form = get_node_form(node_type)
    user_id = current_user.objectid
    node_schema = node_type['dyn_schema'].to_dict()
    form_schema = node_type['form_schema'].to_dict()
    error = ""

    if form.validate_on_submit():
        if process_node_form(
                form, node_id=node_id, node_type=node_type, user=user_id):
            node = Node.find(node_id, api=api)
            flash ('Node "{0}" correctly edited'.format(node.name))
            return redirect(url_for('nodes.index', node_type_name=node_type['name']))
        else:
            error = "Server error"
            print ("Error sending data")
    else:
        print form.errors

    # Populate Form
    form.name.data = node.name
    form.description.data = node.description
    if 'picture' in form:
        form.picture.data = node.picture
    if node.parent:
        form.parent.data = node.parent

    def set_properties(
            node_schema, form_schema, prop_dict, form, prefix=""):
        for prop in node_schema:
            if not prop in prop_dict:
                continue
            schema_prop = node_schema[prop]
            form_prop = form_schema[prop]
            prop_name = "{0}{1}".format(prefix, prop)
            if schema_prop['type'] == 'dict':
                set_properties(
                    schema_prop['schema'],
                    form_prop['schema'],
                    prop_dict[prop_name],
                    form,
                    "{0}__".format(prop_name))
            else:
                try:
                    data = prop_dict[prop]
                except KeyError:
                    print ("{0} not found in form".format(prop_name))
                if schema_prop['type'] == 'datetime':
                    data = datetime.strptime(data, RFC1123_DATE_FORMAT)
                if prop_name in form:
                    form[prop_name].data = data


    prop_dict = node.properties.to_dict()
    set_properties(node_schema, form_schema, prop_dict, form)


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
                error=error)
    except TemplateNotFound:
        template = 'nodes/edit{1}.html'.format(node_type['name'], embed_string)
        return render_template(
                template,
                node=node,
                parent=parent,
                form=form,
                errors=form.errors,
                error=error)


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
        flash('Node "{0}" correctly deleted'.format(name))
        # print (node_type['name'])
        return redirect(url_for('nodes.index', node_type_name=node_type['name']))
    else:
        flash('Forbidden access')
        return redirect(url_for('nodes.edit', node_id=node._id))
