from pillarsdk import Node
from flask import request
from flask import jsonify
from flask import session
from flask.ext.login import login_required
from application.modules.nodes import nodes
from application.modules.nodes import project_update_nodes_list
from application.modules.nodes import view
from application.modules.users.model import UserProxy
from application import SystemUtility
from application import app


@nodes.route('/projects/add-featured-node', methods=['POST'])
@login_required
def projects_add_featured_node():
    node_id = request.form['node_id']
    action = project_update_nodes_list(node_id, list_name='featured')
    return jsonify(status='success', data=dict(action=action))


@nodes.route('/projects/move-node', methods=['POST'])
@login_required
def projects_move_node():
    # Process the move action
    node_id = request.form['node_id']
    dest_parent_node_id = request.form['dest_parent_node_id']

    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)
    node.parent = dest_parent_node_id
    node.update(api=api)
    return jsonify(status='success', data=dict(message='node moved'))


@app.route("/<name>/<project>/")
def project_view(name, project):
    """Entry point to view a project.
    """
    user = UserProxy(name)
    project = user.project(project)
    session['current_project_id'] = project._id
    return view(project._id)
