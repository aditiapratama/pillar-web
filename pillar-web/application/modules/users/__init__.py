import requests
import json
from pillarsdk import utils
from pillarsdk.users import User
from pillarsdk.nodes import Node
from pillarsdk.nodes import NodeType
from pillarsdk.tokens import Token
from pillarsdk.groups import Group

from flask import Blueprint
from flask import render_template
from flask import flash
from flask import session
from flask import redirect
from flask import request
from flask import url_for

from application.modules.users.forms import UserLoginForm
from application.modules.users.forms import UserProfileForm
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
    db_user = User.find(user_id, api=api)
    group = Group.find_one({'where': "name=='subscriber'"}, api=api)
    external_subscriptions_server = app.config['EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER']
    r = requests.get(external_subscriptions_server, params={'blenderid': db_user.email})
    store_user = r.json()

    if store_user['cloud_access'] == 1:
        if db_user.roles and 'subscriber' not in db_user.roles:
            db_user.roles.append('subscriber')
        elif not db_user.roles:
            db_user.roles = ['subscriber',]

        if db_user.groups and group._id not in db_user.groups:
            db_user.groups.append(group._id)
        elif not db_user.groups:
            db_user.groups = [group._id]
        db_user.update(api=api)

    elif db_user.roles and 'admin' not in db_user.roles:
        if db_user.roles and 'subscriber' in db_user.roles:
            db_user.roles.remove('subscriber')

        if db_user.groups and group._id in db_user.groups:
            db_user.groups.remove(group._id)

        db_user.update(api=api)


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

            flash('Welcome {0}!'.format(form.email.data), 'info')
            return redirect('/')
        elif auth:
            flash('{0}'.format(auth['data']), 'danger')
            return redirect('/')
    return render_template('users/login.html', form=form)


@users.route("/logout")
def logout():
    logout_user()
    flash('Successfully logged out', 'info')
    return redirect('/')


@users.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    """Profile view and edit page. This is a temporary implementation.
    """
    api = SystemUtility.attract_api()
    user = User.find(current_user.objectid, api=api)

    form = UserProfileForm(
        full_name = user.full_name)

    if form.validate_on_submit():
        user.full_name = form.full_name.data
        user.update(api=api)
        flash("Profile updated", 'success')

    return render_template('users/profile.html',
                           form=form)


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
