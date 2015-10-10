import time
from flask import request
from flask import jsonify
from flask import render_template
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
            confidence=0,
            rating_positive=0,
            rating_negative=0))

    if parent_id:
        node_asset_props['parent'] = parent_id
    node_asset = Node(node_asset_props)
    node_asset.create(api=api)

    return jsonify(
        asset_id=node_asset._id,
        content=node_asset.properties.content)


def format_comment(comment, is_reply=False, is_team=False, replies=None):
    """Format a comment node into a simpler dictionary.

    :param comment: the comment object
    :param is_reply: True if the comment is a reply to another comment
    :param is_team: True if the author belongs to the group that owns the node
    :param replies: list of replies (formatted with this function)
    """
    is_own = current_user.objectid == comment.user._id
    is_rated = False
    is_rated_positive = None
    if comment.properties.ratings:
        for rating in comment.properties.ratings:
            if rating.user == current_user.objectid:
                is_rated = True
                is_rated_positive = rating.is_positive
                continue
    return dict(_id=comment._id,
        gravatar=gravatar(comment.user.email),
        time_published=comment._created,
        rating_up=comment.properties.rating_positive,
        rating_down=comment.properties.rating_negative,
        author=comment.user.username,
        content=comment.properties.content,
        is_reply=is_reply,
        is_own=is_own,
        is_rated=is_rated,
        is_rated_positive=is_rated_positive,
        is_team=is_team,
        replies=replies)


@nodes.route("/comments/")
@login_required
def comments_index():
    parent_id = request.args.get('parent_id')

    if request.args.get('format'):

        # Get data only if we format it
        api = SystemUtility.attract_api()
        node_type = NodeType.find_first({
            'where': '{"name" : "comment"}',
            }, api=api)

        nodes = Node.all({
            'where': '{"node_type" : "%s", "parent": "%s"}' % (node_type._id, parent_id),
            'embedded': '{"user":1}'}, api=api)

        comments = []
        for comment in nodes._items:

            # Query for first level children (comment replies)
            replies = Node.all({
                'where': '{"node_type" : "%s", "parent": "%s"}' % (node_type._id, comment._id),
                'embedded': '{"user":1}'}, api=api)
            replies = replies._items if replies._items else None

            if replies:
                replies = [format_comment(reply, is_reply=True) for reply in replies]

            comments.append(
                format_comment(comment, is_reply=False, replies=replies))

        if request.args.get('format') == 'json':
            return_content = jsonify(items=comments)
    else:
        # Data will be requested via javascript
        return_content = render_template('asset/_comments.html',
            parent_id=parent_id)
    return return_content


@nodes.route("/comments/<comment_id>/rate", methods=['POST'])
@login_required
def comments_rate(comment_id):
    """Comment rating function

    :param comment_id: the comment id
    :type comment_id: str
    :param rating: the rating (is cast from 0 to False and from 1 to True)
    :type rating: int

    """
    rating_is_positive = False if request.form['is_positive'] == 'false' else True

    api = SystemUtility.attract_api()
    comment = Node.find(comment_id, api=api)

    # Check if comment has been rated
    user_comment_rating = None
    if comment.properties.ratings:
        for rating in comment.properties.ratings:
            if rating['user'] == current_user.objectid:
                user_comment_rating = rating
    #r = next((r for r in comment.ratings if r['user'] == current_user.objectid), None)

    if user_comment_rating:
        # Update or remove rating
        if user_comment_rating['is_positive'] == rating_is_positive:
            # If the rating matches, remove the it
            comment.properties.ratings.remove(user_comment_rating)
            # Update global rating values
            if rating_is_positive:
                comment.properties.rating_positive -= 1
            else:
                comment.properties.rating_negative -= 1
            comment.update(api=api)
            return_data = dict(is_rated=False,
                                rating_up=comment.properties.rating_positive)
        else:
            # If the rating differs from the current, update its value. In this
            # case we make sure we update the existing global rating values as well
            user_comment_rating['is_positive'] = rating_is_positive
            if rating_is_positive:
                comment.properties.rating_positive += 1
                comment.properties.rating_negative -= 1
            else:
                comment.properties.rating_negative += 1
                comment.properties.rating_positive -= 1
            comment.update(api=api)
            return_data = dict(is_positive=rating_is_positive, is_rated=True,
                                rating_up=comment.properties.rating_positive)
    else:
        # Create rating for current user
        user_comment_rating = dict(user=current_user.objectid,
                                    is_positive=rating_is_positive,
                                    # Hardcoded to default (auto valid)
                                    weight=3)
        if not comment.properties.ratings:
            comment.properties.ratings = []
        comment.properties.ratings.append(user_comment_rating)
        if rating_is_positive:
            comment.properties.rating_positive += 1
        else:
            comment.properties.rating_negative += 1
        comment.update(api=api)
        return_data = dict(is_positive=rating_is_positive, is_rated=True,
                            rating_up=comment.properties.rating_positive)

    return jsonify(status='success', data=return_data)

