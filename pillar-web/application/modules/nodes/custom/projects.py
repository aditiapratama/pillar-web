from flask import request
from flask import jsonify
from flask.ext.login import login_required
from application.modules.nodes import nodes
from application.modules.nodes import project_update_nodes_list
from application import SystemUtility


@nodes.route('/projects/<project_id>/add-featured', methods=['POST'])
@login_required
def projects_add_featured(project_id):
    node_id = request.form['node_id']
    project_update_nodes_list(project_id, node_id, list_name='featured')
    return jsonify(status='success', data=dict(project_id=project_id))
