from flask import request
from flask import jsonify
from flask import session
from flask.ext.login import login_required
from flask.ext.login import current_user
from pillarsdk import Node
from pillarsdk import NodeType
from application import SystemUtility
from application.modules.nodes import nodes


@nodes.route('/groups/create', methods=['POST'])
@login_required
def groups_create():
    # Use current_project_id from the session instead of the cookie
    project_id = session['current_project_id']
    name = request.form['name']
    parent_id = request.form.get('parent_id')

    api = SystemUtility.attract_api()
    node_type = NodeType.find_first({
        'where': '{"name" : "group"}',
        }, api=api)
    # We will create the Node object later on, after creating the file object
    node_asset_props = dict(
        name=name,
        user=current_user.objectid,
        node_type=node_type._id,
        project=project_id,
        properties=dict(
            status='published'))

    if parent_id:
        node_asset_props['parent'] = parent_id
    node_asset = Node(node_asset_props)
    node_asset.create(api=api)
    return jsonify(status='success',
        data=dict(name=name, asset_id=node_asset._id))
