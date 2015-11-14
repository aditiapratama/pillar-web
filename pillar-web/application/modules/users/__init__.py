import os
import requests
import json
from pillarsdk import utils
from pillarsdk.users import User
from pillarsdk.nodes import Node
from pillarsdk.nodes import NodeType
from pillarsdk.tokens import Token
from pillarsdk.groups import Group
from pillarsdk.exceptions import ResourceInvalid

from flask import Blueprint
from flask import render_template
from flask import flash
from flask import session
from flask import redirect
from flask import request
from flask import url_for

from application.modules.users.forms import UserLoginForm
from application.modules.users.forms import UserProfileForm
from application.modules.users.forms import UserSettingsEmailsForm
from application.helpers import Pagination

from application import SystemUtility
from application import UserClass
from application import load_user
from application import app

from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import current_user
from flask.ext.login import login_required


# Name of the Blueprint
users = Blueprint('users', __name__)


def authenticate(username, password):
    import requests
    import socket
    payload = dict(
        username=username,
        password=password,
        hostname=socket.gethostname())
    try:
        r = requests.post("{0}/u/identify".format(
            SystemUtility.blender_id_endpoint()), data=payload)
    except requests.exceptions.ConnectionError as e:
        raise e

    if r.status_code == 200:
        response = r.json()
    else:
        response = None
    return response


def user_roles_update(user_id):
    api = SystemUtility.attract_api()
    user = User.find(user_id, api=api)
    group_subscriber = Group.find_one({'where': "name=='subscriber'"}, api=api)
    external_subscriptions_server = app.config['EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER']
    r = requests.get(external_subscriptions_server, params={'blenderid': user.email})
    store_user = r.json()

    if store_user['cloud_access'] == 1:
        if user.roles and 'subscriber' not in user.roles:
            user.roles.append('subscriber')
        elif not user.roles:
            user.roles = ['subscriber',]

        if user.groups and group_subscriber._id not in user.groups:
            user.groups.append(group_subscriber._id)
        elif not user.groups:
            user.groups = [group_subscriber._id]
        user.update(api=api)
        return
    elif user.roles and 'admin' not in user.roles:
        if user.roles and 'subscriber' in user.roles:
            user.roles.remove('subscriber')

        if user.groups and group_subscriber._id in user.groups:
            user.groups.remove(group_subscriber._id)
        user.update(api=api)
        return

    # Custom demo list functionality, only available is a DEMO_USER_LIST is
    # available. The content of the file is a list of email addresses. One
    # address per line.
    if 'DEMO_USERS_LIST' in app.config:
        users_list_filepath = app.config['DEMO_USERS_LIST']
        if os.path.isfile(users_list_filepath):
            group_demo = Group.find_one({'where': "name=='demo'"}, api=api)
            # Load all emails in a list for lookup
            emails = [l.rstrip('\n') for l in open(users_list_filepath)]
            if user.email in emails:
                if not user.groups:
                    user.groups = []
                user.groups.append(group_demo._id)
                user.update(api=api)


@users.route("/login", methods=['GET', 'POST'])
def login():
    form = UserLoginForm()
    if form.validate_on_submit():
        auth = authenticate(form.email.data, form.password.data)
        if auth and auth['status'] == 'success':
            user = UserClass(auth['data']['token'])
            login_user(user)
            user = load_user(current_user.id)
            # Check with the store for user roles. If the user has an active
            # subscription, we apply the 'subscriber' role
            user_roles_update(user.objectid)
            # flash('Welcome {0}!'.format(form.email.data), 'info')
            return redirect(url_for('homepage'))
        elif auth:
            flash('{0}'.format(auth['data']), 'danger')
            return redirect(url_for('users.login'))
    return render_template('users/login.html', form=form)


@users.route("/logout")
def logout():
    logout_user()
    # flash('Successfully logged out', 'info')
    return redirect('/')


@users.route("/settings/profile", methods=['GET', 'POST'])
@login_required
def settings_profile():
    """Profile view and edit page. This is a temporary implementation.
    """
    api = SystemUtility.attract_api()
    user = User.find(current_user.objectid, api=api)

    form = UserProfileForm(
        full_name = user.full_name,
        username = user.username)

    if form.validate_on_submit():
        try:
           user.full_name = form.full_name.data
           user.username = form.username.data
           user.update(api=api)
           flash("Profile updated", 'success')
        except ResourceInvalid as e:
            message = json.loads(e.content)
            flash(message)

    return render_template('users/settings/profile.html', form=form, title='profile')


@users.route("/settings/emails", methods=['GET', 'POST'])
@login_required
def settings_emails():
    """Main email settings
    """
    api = SystemUtility.attract_api()
    user = User.find(current_user.objectid, api=api)

    # Force creation of settings for the user (safely remove this code once
    # implemented on account creation level, and after adding settings to all
    # existing users)
    if not user.settings:
        user.settings = dict(email_communications=1)
        user.update(api=api)

    if user.settings.email_communications == None:
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
        except ResourceInvalid as e:
            message = json.loads(e.content)
            flash(message)

    return render_template('users/settings/emails.html', form=form, title='emails')


@users.route("/settings/billing")
@login_required
def settings_billing():
    """View the subscription status of a user
    """
    api = SystemUtility.attract_api()
    user = User.find(current_user.objectid, api=api)
    group = Group.find_one({'where': "name=='subscriber'"}, api=api)
    external_subscriptions_server = app.config['EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER']
    r = requests.get(external_subscriptions_server, params={'blenderid': user.email})
    store_user = r.json()
    return render_template('users/settings/billing.html', store_user=store_user, title='billing')


def type_names():
    api = SystemUtility.attract_api()

    types = NodeType.all(api=api)["_items"]
    type_names = []
    for names in types:
        type_names.append(str(names['name']))
    return type_names


@users.route("/tasks", methods=['GET', 'POST'])
@login_required
def tasks():
    """User-assigned tasks"""
    # Pagination index
    page = request.args.get('page', 1)
    max_results = 50

    api = SystemUtility.attract_api()
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
