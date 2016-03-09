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
from pillarsdk.activities import Notification
from pillarsdk.activities import ActivitySubscription
from application import app
from application import SystemUtility
from application.helpers import pretty_date

# Name of the Blueprint
notifications = Blueprint('notifications', __name__)


def notification_parse(notification):
    api = SystemUtility.attract_api()
    actor = User.find(notification.actor, api=api)
    return dict(
        _id=notification._id,
        username=actor.username,
        username_avatar=actor.gravatar(),
        action=notification.action,
        object_type=notification.object_type,
        object_name=notification.object_name,
        object_url=url_for(
            'nodes.view', node_id=notification.object_id, redir=1),
        context_object_type=notification.context_object_type,
        context_object_name=notification.context_object_name,
        context_object_url=url_for(
            'nodes.view', node_id=notification.context_object_id, redir=1),
        date=pretty_date(notification._created),
        is_read=notification.is_read,
        is_subscribed=notification.is_subscribed,
        subscription=notification.subscription
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
        'max_results': str(limit),
        'parse': '1'}, api=api)
    notifications = notifications._items
    items = [notification_parse(n) for n in notifications]

    return jsonify(items=items)


@notifications.route('/<notification_id>/read-toggle')
@login_required
def action_read_toggle(notification_id):
    api = SystemUtility.attract_api()
    notification = Notification.find(notification_id, api=api)
    if notification.user == current_user.objectid:
        notification.is_read = not notification.is_read
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
        'where': '{"user": "%s"}' % (current_user.objectid),
        'sort': '-_created'}, api=api)

    for notification in notifications._items:
        notification = Notification.find(notification._id, api=api)
        notification.is_read = True
        notification.update(api=api)

    return jsonify(status='success',
        data=dict(
            message="All notifications mark as read"))


@notifications.route('/<notification_id>/subscription-toggle')
@login_required
def action_subscription_toggle(notification_id):
    """Given a notification id, get the ActivitySubscription and update it by
    toggling the notifications status for the web key.
    """
    api = SystemUtility.attract_api()
    # Get the notification
    notification = notification_parse(
        Notification.find(notification_id, api=api))
    # Get the subscription and modify it
    subscription = ActivitySubscription.find(
        notification['subscription'], api=api)
    subscription.notifications['web'] = not subscription.notifications['web']
    subscription.update(api=api)
    return jsonify(status='success',
        data=dict(
            message="You have been {}subscribed".format(
                '' if subscription.notifications['web'] else 'un')))
