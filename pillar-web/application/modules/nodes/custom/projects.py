from pillarsdk import Node
from pillarsdk.exceptions import ResourceNotFound
from flask import request
from flask import jsonify
from flask import session
from flask import abort
from flask.ext.login import login_required
from application import SystemUtility
from application import app
from application import cache
from application.modules.nodes import nodes
from application.modules.nodes import project_update_nodes_list
from application.modules.nodes import view
from application.modules.users.model import UserProxy
from application.helpers import current_user_is_authenticated


@nodes.route('/projects/add-featured-node', methods=['POST'])
@login_required
def projects_add_featured_node():
    """Feature a node in a project. This method belongs here, because it affects
    the project node itself, not the asset.
    """
    api = SystemUtility.attract_api()
    node = Node.find(request.form['node_id'], api=api)
    action = project_update_nodes_list(node, list_name='featured')
    return jsonify(status='success', data=dict(action=action))


@nodes.route('/projects/move-node', methods=['POST'])
@login_required
def projects_move_node():
    """Move a node within a project. While this affects the node.parent prop, we
    keep it in the scope of the project."""
    node_id = request.form['node_id']
    dest_parent_node_id = request.form['dest_parent_node_id']

    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)
    node.parent = dest_parent_node_id
    node.update(api=api)
    return jsonify(status='success', data=dict(message='node moved'))


@nodes.route('/projects/delete-node', methods=['POST'])
@login_required
def projects_delete_node():
    """Delete a node"""
    api = SystemUtility.attract_api()
    node = Node.find(request.form['node_id'], api=api)
    if node.has_method('PUT'):
        node.properties.status = 'deleted'
        # Temporarily append a [D] at the name. We will properly display the node
        # status from the properties later on.
        node.name = u"[D] {0}".format(node.name)
        node.update(api=api)
        return jsonify(status='success', data=dict(message='Node delete'))
    else:
        return abort(403)


@nodes.route('/projects/toggle-node-public', methods=['POST'])
@login_required
def projects_toggle_node_public():
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
        return jsonify(status='success', data=dict(message=message))
    else:
        return abort(403)


@app.route("/p/<project_url>/")
@cache.cached(timeout=3600, unless=current_user_is_authenticated)
def project_view(project_url):
    """Entry point to view a project"""
    api = SystemUtility.attract_api()
    try:
        project = Node.find_one({
            'where': '{"properties.url" : "%s"}' % (project_url)}, api=api)
        session['current_project_id'] = project._id
        return view(project._id)
    except ResourceNotFound:
        return abort(404)
