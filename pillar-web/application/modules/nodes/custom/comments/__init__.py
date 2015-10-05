import time
from flask import request
from flask import jsonify
from flask.ext.login import login_required
from flask.ext.login import current_user
from pillarsdk import Node
from pillarsdk import NodeType
from application.modules.nodes import nodes
from application.helpers import gravatar
from application import SystemUtility


@nodes.route('/comments/create', methods=['POST'])
@login_required
def comments_create():
    content = request.form['content']
    parent_id = request.form.get('parent_id')

    api = SystemUtility.attract_api()
    node_type = NodeType.find_first({
        'where': '{"name" : "comment"}',
        }, api=api)

    node_asset_props = dict(
        name='Comment',
        #description=a.description,
        #picture=picture,
        user=current_user.objectid,
        node_type=node_type._id,
        #parent=node_parent,
        properties=dict(
            content=content,
            status='published',
            confidence=0))

    if parent_id:
        node_asset_props['parent'] = parent_id
    node_asset = Node(node_asset_props)
    node_asset.create(api=api)

    return jsonify(
        asset_id=node_asset._id,
        content=node_asset.properties.content)


@nodes.route("/comments/index.json")
@login_required
def comments_index():
    parent_id = request.args.get('parent_id')
    api = SystemUtility.attract_api()
    node_type = NodeType.find_first({
        'where': '{"name" : "comment"}',
        }, api=api)

    nodes = Node.all({
        'where': '{"node_type" : "%s", "parent": "%s"}' % (node_type._id, parent_id),
        'embedded': '{"user":1}'}, api=api)

    comments = []
    for comment in nodes._items:
        is_own = False
        if current_user.objectid == comment.user._id:
            is_own = True
        is_reply = False
        # TODO (parse parent and check if it's a comment node_type)
        comments.append(
            dict(_id=comment._id,
                gravatar=gravatar(comment.user.email),
                time_published=comment._created,
                rating_up=comment.properties.rating_positive,
                rating_down=comment.properties.rating_negative,
                author=comment.user.username,
                content=comment.properties.content,
                is_reply=is_reply,
                is_own=is_own,
                is_team=False))
    return jsonify(items=comments)
