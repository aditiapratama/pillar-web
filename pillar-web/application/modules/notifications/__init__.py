from flask import jsonify
from flask import Blueprint
from flask import request
from flask import url_for
from flask import abort
from flask.ext.login import login_required
from flask.ext.login import current_user
from pillarsdk.users import User
from pillarsdk.nodes import Node
from pillarsdk.projects import Project
from pillarsdk.activities import Activity
from pillarsdk.activities import Notification
from application import app
from application import SystemUtility
from application.helpers import pretty_date

# Name of the Blueprint
notifications = Blueprint('notifications', __name__)


def notification_parse(notification):
    api = SystemUtility.attract_api()
    # Get activity with embedded user (or maybe not needed)
    activity = Activity.find(notification.activity, api=api)
    actor = User.find(activity.actor_user, api=api)

    # Context is optional
    context_object_type = None
    context_object_name = None
    context_object_url = None

    if activity.object_type == 'node':
        node = Node.find(activity.object, api=api)
        # project = Project.find(node.project, {
        #     'projection': '{"name":1, "url":1}'}, api=api)
        # Initial support only for node_type comments
        if node.node_type == 'comment':
            # comment = Comment.query.get_or_404(notification_object.object_id)
            node.parent = Node.find(node.parent, api=api)
            object_type = 'comment'
            object_name = ''

            object_url = url_for('nodes.view', node_id=node._id, redir=1)
            if node.parent.user == current_user.objectid:
                owner = "your {0}".format(node.parent.node_type)
            else:
                parent_comment_user = User.find(node.parent.user, api=api)
                owner = "{0}'s {1}".format(parent_comment_user.username,
                    node.parent.node_type)

            context_object_type = node.parent.node_type
            context_object_url = url_for('nodes.view', node_id=activity.context_object, redir=1)

            if context_object_type == 'post':
                context_object_name = '{0} "{1}"'.format(owner, node.parent.name)
            else:
                context_object_name = owner


            if activity.verb == 'replied':
                action = 'replied to'
            elif activity.verb == 'commented':
                action = 'left a comment on'
            else:
                action = activity.verb
        else:
            return None
    else:
        return None

    return dict(
        _id=notification._id,
        username=actor.username,
        username_avatar=actor.gravatar(),
        action=action,
        object_type=object_type,
        object_name=object_name,
        object_url=object_url,
        context_object_type=context_object_type,
        context_object_name=context_object_name,
        context_object_url=context_object_url,
        date=pretty_date(activity._created),
        is_read=notification.is_read,
        # is_subscribed=notification.is_subscribed
        )


@notifications.route('/')
@login_required
def index():
    """Get notifications for the current user.

    Optional url args:
    - limit: limits the number of notifications
    """
    limit = request.args.get('limit', 25)
    api = SystemUtility.attract_api()
    notifications = Notification.all({
        'where': '{"user": "%s"}' % (current_user.objectid),
        'sort': '-_created',
        'max_results': str(limit)}, api=api)
    notifications = notifications._items
    items = [notification_parse(n) for n in notifications]

    return jsonify(items=items)


@notifications.route('/<notification_id>/read-toggle')
@login_required
def action_read_toggle(notification_id):
    api = SystemUtility.attract_api()
    notification = Notification.find(notification_id, api=api)
    if notification.user == current_user.objectid:
        if notification.is_read:
            notification.is_read = False
        else:
            notification.is_read = True
        notification.update(api=api)
        return jsonify(
            status='success',
            data=dict(
                message="Notification {0} is_read {1}".format(
                    notification_id,
                    notification.is_read),
                is_read=notification.is_read))
    else:
        return abort(403)


@notifications.route('/read-all')
@login_required
def action_read_all():
    """Mark all notifications as read"""
    api = SystemUtility.attract_api()
    notifications = Notification.all({
        'where': '{"user": "%s"}' % (current_user.objectid)}, api=api)

    for notification in notifications._items:
        notification = Notification.find(notification._id, api=api)
        notification.is_read = True
        notification.update(api=api)

    return jsonify(status='success',
        data=dict(
            message="All notifications mark as read"))


@notifications.route('/<activity_id>/subscription-toggle')
@login_required
def action_subscription_toggle(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id == current_user.id:
        notification_subscription = notification.get_subscription()
        if notification_subscription:
            if notification_subscription.is_subscribed:
                notification_subscription.is_subscribed = False
                action = "Unsubscribed"
            else:
                notification_subscription.is_subscribed = True
                action = "Subscribed"
            db.session.commit()
            return jsonify(message="{0} from notifications".format(action))
        else:
            return jsonify(message="No subscription exists")
    else:
        return abort(403)
