import requests
import json
import logging

from flask.ext.oauthlib.client import OAuthException

from pillarsdk.users import User
from pillarsdk.nodes import Node
from pillarsdk.nodes import NodeType
from pillarsdk.groups import Group
from pillarsdk import exceptions as sdk_exceptions

from flask import Blueprint
from flask import render_template
from flask import flash
from flask import session
from flask import redirect
from flask import request
from flask import url_for
from flask import abort

from application.modules.users.forms import UserLoginForm
from application.modules.users.forms import UserProfileForm
from application.modules.users.forms import UserSettingsEmailsForm
from application.modules.users.forms import UserEditForm

from application import system_util
from application import UserClass
from application import load_user
from application import app
from application import blender_id

from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import current_user
from flask.ext.login import login_required


# Name of the Blueprint
users = Blueprint('users', __name__)
log = logging.getLogger(__name__)


def authenticate(username, password):
    import requests
    import socket
    payload = dict(
        username=username,
        password=password,
        hostname=socket.gethostname())
    try:
        r = requests.post("{0}/u/identify".format(
            system_util.blender_id_endpoint()), data=payload)
    except requests.exceptions.ConnectionError as e:
        raise e

    if r.status_code == 200:
        return r.json()
    return None


def user_roles_update(user_id):
    api = system_util.pillar_api()
    group_subscriber = Group.find_one({'where': "name=='subscriber'"}, api=api)

    external_subscriptions_server = app.config['EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER']

    # Fetch the user once outside the loop, because we only need to get the
    # subscription status once.
    user = User.me(api=api)

    r = requests.get(external_subscriptions_server, params={'blenderid': user.email})
    if r.status_code != 200:
        log.warning("Error communicating with %s, code=%i, unable to check "
                    "subscription status of user %s",
                    external_subscriptions_server, r.status_code, user_id)
        return
    store_user = r.json()

    max_retry = 5
    for retry_count in range(max_retry):
        # Update the user's role & groups for their subscription status.
        roles = set(user.roles or [])
        groups = set(user.groups or [])

        if store_user['cloud_access'] == 1:
            roles.add(u'subscriber')
            groups.add(group_subscriber._id)

        elif u'admin' not in roles:
            roles.discard(u'subscriber')
            groups.discard(group_subscriber._id)

        # Only send an API request when the user has actually changed
        if set(user.roles or []) == roles and set(user.groups or []) == groups:
            break

        user.roles = list(roles)
        user.groups = list(groups)

        try:
            user.update(api=api)
        except sdk_exceptions.PreconditionFailed:
            log.warning('User etag changed while updating roles, retrying.')
        else:
            # Successful update, so we can stop the loop.
            break

        # Fetch the user for the next iteration.
        if retry_count < max_retry - 1:
            user = User.me(api=api)
    else:
        log.warning('Tried %i times to update user %s, and failed each time. Giving up.',
                    max_retry, user_id)


@users.route('/logout')
def logout():
    logout_user()
    session.clear()
    # flash('Successfully logged out', 'info')
    return redirect('/')


def check_oauth_provider(provider):
    if not provider:
        return abort(404)


@users.route('/login')
def login():
    check_oauth_provider(blender_id)
    callback = url_for(
        'users.blender_id_authorized',
        next=None,
        _external=True,
        _scheme=app.config['SCHEME']
    )
    return blender_id.authorize(callback=callback)


@users.route('/login/local', methods=['GET', 'POST'])
def login_local():
    """Login with a local account, skipping OAuth. This provides access only
    to the web application and is meant for limited access (for example in
    the case of a shared account)."""
    form = UserLoginForm()
    # Forward credentials to server
    if form.validate_on_submit():
        payload = {
            'username': form.username.data,
            'password': form.password.data
            }
        r = requests.post("{0}/auth/make-token".format(
            system_util.pillar_server_endpoint()), data=payload)
        if r.status_code != 200:
            return abort(r.status_code)
        res = r.json()
        # If correct, receive token and log in the user
        user = UserClass(res['token'])
        login_user(user)
        return redirect(url_for('homepage'))
    return render_template('users/login.html', form=form)


@users.route('/oauth/blender-id/authorized')
def blender_id_authorized():
    check_oauth_provider(blender_id)
    oauth_resp = blender_id.authorized_response()
    if oauth_resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(oauth_resp, OAuthException):
        return 'Access denied: %s' % oauth_resp.message

    session['blender_id_oauth_token'] = (oauth_resp['access_token'], '')

    user = UserClass(oauth_resp['access_token'])
    login_user(user)
    user = load_user(current_user.id)
    # Check with the store for user roles. If the user has an active
    # subscription, we apply the 'subscriber' role
    user_roles_update(user.objectid)
    # flash('Welcome %(first_name)s %(last_name)s!' % user_data.data, 'info')
    return redirect(url_for('homepage'))

if blender_id:
    @blender_id.tokengetter
    def get_blender_id_oauth_token():
        return session.get('blender_id_oauth_token')


@users.route('/settings/profile', methods=['GET', 'POST'])
@login_required
def settings_profile():
    """Profile view and edit page. This is a temporary implementation.
    """
    if current_user.has_role('protected'):
        return abort(404)  # TODO: make this 403, handle template properly
    api = system_util.pillar_api()
    user = User.find(current_user.objectid, api=api)

    form = UserProfileForm(
        full_name=user.full_name,
        username=user.username)

    if form.validate_on_submit():
        try:
            user.full_name = form.full_name.data
            user.username = form.username.data
            user.update(api=api)
            flash("Profile updated", 'success')
        except sdk_exceptions.ResourceInvalid as e:
            message = json.loads(e.content)
            flash(message)

    return render_template('users/settings/profile.html', form=form, title='profile')


@users.route('/settings/emails', methods=['GET', 'POST'])
@login_required
def settings_emails():
    """Main email settings.
    """
    if current_user.has_role('protected'):
        return abort(404)  # TODO: make this 403, handle template properly
    api = system_util.pillar_api()
    user = User.find(current_user.objectid, api=api)

    # Force creation of settings for the user (safely remove this code once
    # implemented on account creation level, and after adding settings to all
    # existing users)
    if not user.settings:
        user.settings = dict(email_communications=1)
        user.update(api=api)

    if user.settings.email_communications is None:
        user.settings.email_communications = 1
        user.update(api=api)

    # Generate form
    form = UserSettingsEmailsForm(
        email_communications=user.settings.email_communications)

    if form.validate_on_submit():
        try:
            user.settings.email_communications = form.email_communications.data
            user.update(api=api)
            flash("Profile updated", 'success')
        except sdk_exceptions.ResourceInvalid as e:
            message = json.loads(e.content)
            flash(message)

    return render_template('users/settings/emails.html', form=form, title='emails')


@users.route('/settings/billing')
@login_required
def settings_billing():
    """View the subscription status of a user
    """
    if current_user.has_role('protected'):
        return abort(404)  # TODO: make this 403, handle template properly
    api = system_util.pillar_api()
    user = User.find(current_user.objectid, api=api)
    groups = []
    if user.groups:
        for group_id in user.groups:
            group = Group.find(group_id, api=api)
            groups.append(group.name)
    external_subscriptions_server = app.config['EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER']
    r = requests.get(external_subscriptions_server, params={'blenderid': user.email})
    store_user = r.json()
    return render_template('users/settings/billing.html',
        store_user=store_user, groups=groups, title='billing')


def type_names():
    api = system_util.pillar_api()

    types = NodeType.all(api=api)["_items"]
    type_names = []
    for names in types:
        type_names.append(str(names['name']))
    return type_names


@users.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    """User-assigned tasks"""
    # Pagination index
    page = request.args.get('page', 1)
    max_results = 50

    api = system_util.pillar_api()
    node_type_list = NodeType.all({'where': "name=='task'"}, api=api)

    if len(node_type_list['_items']) == 0:
        return "Empty NodeType list", 200

    node_type = node_type_list._items[0]

    tasks = Node.all({
        'where': '{"node_type" : "%s", "properties.owners.users": {"$in": ["%s"]}}'\
                % (node_type['_id'], current_user.objectid),
        'max_results': max_results,
        'page': page,
        'embedded': '{"parent":1, "picture":1}',
        'sort' : "order"}, api=api)

    # Build the pagination object
    # pagination = Pagination(int(page), max_results, tasks._meta.total)

    tasks_datatable = []
    for task in tasks._items:
        cut_in = 0
        cut_out = 0
        if task.parent.properties.cut_in:
            cut_in = task.parent.properties.cut_in
        if task.parent.properties.cut_out:
            cut_out = task.parent.properties.cut_out
        data = {
            'DT_RowId': "row_{0}".format(task._id),
            '_id': task._id,
            'order': task.order,
            'picture': None,
            'name': task.name,
            'timing': {
                'cut_in': task.parent.properties.cut_in,
                'cut_out': task.parent.properties.cut_out,
            },
            'parent': task.parent.to_dict(),
            'description': task.description,
            'url_view': url_for('nodes.view', node_id=task._id),
            'url_edit': url_for('nodes.edit', node_id=task._id, embed=1),
            'status': task.properties.status,
            }

        tasks_datatable.append(data)

    return render_template(
        'users/tasks.html',
        title="task",
        tasks_data=json.dumps(tasks_datatable),
        node_type=node_type)


@users.route('/u')
@login_required
def users_index():
    if not current_user.has_role('admin'):
        return abort(403)
    return render_template('users/index.html')

@users.route('/u/<user_id>/edit', methods=['GET', 'POST'])
@login_required
def users_edit(user_id):
    if not current_user.has_role('admin'):
        return abort(403)
    api = system_util.pillar_api()
    user = User.find(user_id, api=api)
    form = UserEditForm()
    if form.validate_on_submit():
        def get_groups(roles):
            """Return a set of role ids matching the group names provided"""
            groups_set = set()
            for system_role in roles:
                group = Group.find_one({'where': "name=='%s'" % system_role}, api=api)
                groups_set.add(group._id)
            return groups_set

        # Remove any of the default roles
        system_roles = set([role[0] for role in form.roles.choices])
        system_groups = get_groups(system_roles)
        # Current user roles
        user_roles_list = user.roles if user.roles else []
        user_roles = set(user_roles_list)
        user_groups = get_groups(user_roles_list)
        # Remove all form roles from current roles
        user_roles = list(user_roles.difference(system_roles))
        user_groups = list(user_groups.difference(system_groups))
        # Get the assigned roles
        system_roles_assigned = form.roles.data
        system_groups_assigned = get_groups(system_roles_assigned)
        # Reassign roles based on form.roles.data by adding them to existing roles
        user_roles += system_roles_assigned
        user_groups += list(get_groups(user_roles))
        # Fetch the group for the assigned system roles
        user.roles = user_roles
        user.groups = user_groups
        user.update(api=api)
    else:
        form.roles.data = user.roles
    return render_template('users/edit_embed.html',
        user=user,
        form=form)
