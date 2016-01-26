from pillarsdk import Node
from pillarsdk import Project
from pillarsdk.exceptions import ResourceNotFound
from pillarsdk.exceptions import ForbiddenAccess
from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify
from flask import session
from flask import abort
from flask import g
from flask import redirect
from flask import url_for
from flask.ext.login import login_required
from flask.ext.login import current_user
from application import app
from application import cache
from application import SystemUtility
from application.modules.users.model import UserProxy
from application.modules.projects.forms import ProjectForm
from application.helpers import current_user_is_authenticated
from application.helpers import get_file
from application.helpers import attach_project_pictures
from application.helpers.jstree import jstree_parse_node
from application.helpers.caching import delete_redis_cache_template

projects = Blueprint('projects', __name__)

@projects.route('/<project_url>/')
def view(project_url):
    """Entry point to view a project"""
    api = SystemUtility.attract_api()
    # Fetch the Node or 404
    try:
        project = Project.find_one({
            'where': '{"url" : "%s"}' % (project_url)}, api=api)
    except ResourceNotFound:
        return abort(404)
    # Set up variables for processing
    user_id = 'ANONYMOUS' if current_user.is_anonymous() else str(current_user.objectid)
    rewrite_url = None
    embedded_node_id = None

    if request.args.get('redir') and request.args.get('redir') == '1':
        # Handle special cases (will be mainly used for items that are part
        # of the blog, or attract)
        if g.get('embedded_node')['node_type'] == 'post':
            # Very special case of the post belonging to the main project,
            # which is read from the configuration.
            if project._id == app.config['MAIN_PROJECT_ID']:
                return redirect(url_for('main_blog',
                    url=g.get('embedded_node')['properties']['url']))
            else:
                return redirect(url_for('project_blog',
                    project_url=project.url,
                    url=g.get('embedded_node')['properties']['url']))
        rewrite_url = "/p/{0}/#{1}".format(project.url,
            g.get('embedded_node')['_id'])
        embedded_node_id = g.get('embedded_node')['_id']

    if request.args.get('format') == 'jstree':
        children_list = []
        children = Node.all({
            'projection': '{"name": 1, "parent": 1, "node_type": 1, \
                "properties.order": 1, "properties.status": 1, \
                "properties.content_type": 1, "user": 1, "project": 1}',
            'where': '{"project": "%s", "parent" : {"$exists": false}}' % project._id,
            'sort': 'properties.order'}, api=api)
        for child in children._items:
            # Skip nodes of type comment
            if child.node_type not in ['comment', 'post']:
                # children_list.append(jstree_parse_node(child))
                if child.properties.status == 'published':
                    children_list.append(jstree_parse_node(child))
                elif child.node_type == 'blog':
                    children_list.append(jstree_parse_node(child))
                elif current_user.is_authenticated() and child.user == current_user.objectid:
                    children_list.append(jstree_parse_node(child))
        return jsonify(items=children_list)

    project.picture_square = get_file(project.picture_square)
    project.picture_header = get_file(project.picture_header)
    embed_string = ''

    if request.args.get('embed'):
        embed_string = '_embed'
        list_latest = []
        for node_id in project.nodes_latest:
            try:
                node_item = Node.find(node_id, {
                    'projection': '{"name":1, "user":1, "node_type":1, \
                        "project": 1}',
                    'embedded': '{"user":1}',
                    }, api=api)
                list_latest.append(node_item)
            except ForbiddenAccess:
                list_latest.append(FakeNodeAsset())
        project.nodes_latest = list(reversed(list_latest))

        list_featured = []
        for node_id in project.nodes_featured:
            try:
                node_item = Node.find(node_id, {
                    'projection': '{"name":1, "user":1, "picture":1, \
                        "node_type":1, "project": 1}',
                    'embedded': '{"user":1}',
                    }, api=api)
                if node_item.picture:
                    picture = get_file(node_item.picture)
                    # picture = File.find(node_item.picture, api=api)
                    node_item.picture = picture
                list_featured.append(node_item)
            except ForbiddenAccess:
                list_featured.append(FakeNodeAsset())
        project.nodes_featured = list(reversed(list_featured))

        list_blog = []
        for node_id in project.nodes_blog:
            try:
                node_item = Node.find(node_id, {
                    # 'projection': '{"name":1, "user":1, "node_type":1}',
                    'embedded': '{"user":1}',
                    }, api=api)
                list_blog.append(node_item)
            except ForbiddenAccess:
                list_blog.append(FakeNodeAsset())
        project.nodes_blog = list(reversed(list_blog))

    return render_template("projects/view{0}.html".format(embed_string),
        embedded_node_id=embedded_node_id,
        rewrite_url=rewrite_url,
        user_string_id=user_id,
        project=project,
        api=api)


@projects.route('/<project_url>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_url):
    api = SystemUtility.attract_api()
    # Fetch the Node or 404
    try:
        project = Project.find_one({
            'where': '{"url" : "%s"}' % (project_url)}, api=api)
    except ResourceNotFound:
        return abort(404)
    attach_project_pictures(project, api)
    form = ProjectForm()

    if form.validate_on_submit():
        project = Project.find(project._id, api=api)
        project.name = form.name.data
        if form.picture_square.data:
            project.picture_square = form.picture_square.data
        project.update(api=api)
    else:
        form.project_id.data = project._id
        form.name.data = project.name
        form.url.data = project.url
        form.summary.data = project.summary
        form.description.data = project.description
        form.is_private.data = project.is_private
        form.category.data = project.category
        form.status.data = project.status
        if project.picture_square:
            form.picture_square.data = project.picture_square._id
        if project.picture_header:
            form.picture_header.data = project.picture_header._id

    # List of fields from the form that should be displayed in the sidebar
    sidebar_selection = ['name', 'url', 'status', 'is_private', 'category']
    return render_template('projects/edit.html',
        form=form,
        sidebar_selection=sidebar_selection,
        project=project,
        api=api)


@projects.route('/e/add-featured-node', methods=['POST'])
@login_required
def add_featured_node():
    """Feature a node in a project. This method belongs here, because it affects
    the project node itself, not the asset.
    """
    api = SystemUtility.attract_api()
    node = Node.find(request.form['node_id'], api=api)
    action = project_update_nodes_list(node, list_name='featured')
    return jsonify(status='success', data=dict(action=action))


@projects.route('/e/move-node', methods=['POST'])
@login_required
def move_node():
    """Move a node within a project. While this affects the node.parent prop, we
    keep it in the scope of the project."""
    node_id = request.form['node_id']
    dest_parent_node_id = request.form.get('dest_parent_node_id')

    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)
    # Get original parent id for clearing template fragment on success
    previous_parent_id = node.parent
    if dest_parent_node_id:
        node.parent = dest_parent_node_id
    elif node.parent:
        node.parent = None
    node.update(api=api)
    # Delete cached parent template fragment
    if node.parent:
        delete_redis_cache_template('group_view', node.parent)
    if previous_parent_id:
        delete_redis_cache_template('group_view', previous_parent_id)
    return jsonify(status='success', data=dict(message='node moved'))


@projects.route('/e/delete-node', methods=['POST'])
@login_required
def delete_node():
    """Delete a node"""
    api = SystemUtility.attract_api()
    node = Node.find(request.form['node_id'], api=api)
    if node.has_method('PUT'):
        node.properties.status = 'deleted'
        # Temporarily append a [D] at the name. We will properly display the node
        # status from the properties later on.
        node.name = u"[D] {0}".format(node.name)
        node.update(api=api)
        # Delete cached parent template fragment
        if node.parent:
            delete_redis_cache_template('group_view', node.parent)
        return jsonify(status='success', data=dict(message='Node deleted'))
    else:
        return abort(403)


@projects.route('/e/toggle-node-public', methods=['POST'])
@login_required
def toggle_node_public():
    """Give a node GET permissions for the world. Later on this can turn into
    a more powerful permission management function.
    """
    api = SystemUtility.attract_api()
    node = Node.find(request.form['node_id'], api=api)
    if node.has_method('PUT'):
        if node.permissions and 'world' in node.permissions.to_dict():
            node.permissions = {}
            message = "Node is not public anymore."
        else:
            node.permissions = dict(world=['GET'])
            message = "Node is now public!"
        node.update(api=api)
        # Delete cached parent template fragment
        delete_redis_cache_template('group_view', node.parent)
        return jsonify(status='success', data=dict(message=message))
    else:
        return abort(403)


def project_update_nodes_list(node, project_id=None, list_name='latest'):
    """Update the project node with the latest edited or favorited node.
    The list value can be 'latest' or 'featured' and it will determined where
    the node reference will be placed in.
    """
    if node.properties.status and node.properties.status == 'published':
        if not project_id and 'current_project_id' in session:
            project_id = session['current_project_id']
        elif not project_id:
            return None
        project_id = node.project
        if type(project_id) is not unicode:
            project_id = node.project._id
        api = SystemUtility.attract_api()
        project = Project.find(project_id, api=api)
        if list_name == 'latest':
            nodes_list = project.nodes_latest
        elif list_name == 'blog':
            nodes_list = project.nodes_blog
        else:
            nodes_list = project.nodes_featured

        if not nodes_list:
            node_list_name = 'nodes_' + list_name
            project[node_list_name] = []
            nodes_list = project[node_list_name]
        elif len(nodes_list) > 5:
            nodes_list.pop(0)

        if node._id in nodes_list:
            # Pop to put this back on top of the list
            nodes_list.remove(node._id)
            if list_name == 'featured':
                # We treat the action as a toggle and do not att the item back
                project.update(api=api)
                return "removed"

        nodes_list.append(node._id)
        project.update(api=api)
        return "added"
