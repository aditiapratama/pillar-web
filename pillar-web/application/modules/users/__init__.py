import json
from pillarsdk import utils
from pillarsdk.users import User
from pillarsdk.nodes import Node
from pillarsdk.nodes import NodeType
from pillarsdk.tokens import Token

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
from application import userClass

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
            message = r.json()['message']
            if 'token' in r.json():
                authenticated = True
                token = r.json()['token']
            else:
                authenticated = False
                token = None
        else:
            message = ""
            authenticated = False
            token = None
        return dict(authenticated=authenticated, message=message, token=token)


@users.route("/login", methods=['GET', 'POST'])
def login():
    form = UserLoginForm()
    if form.validate_on_submit():
        token = authenticate(form.email.data, form.password.data)['token']
        if token:
            user = userClass(token)
            login_user(user)
            flash('Welcome {0}!'.format(form.email.data))
            return redirect('/')
    return render_template('users/login.html', form=form)


@users.route("/logout")
def logout():
    logout_user()
    flash('Bye!')
    return redirect('/')


@users.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    """Profile view and edit page. This is a temporary implementation.
    """
    api = SystemUtility.attract_api()
    user = User.find(current_user.objectid, api=api)

    form = UserProfileForm(
        first_name = user.first_name,
        last_name = user.last_name)

    if form.validate_on_submit():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.update(api=api)
        flash("Profile updated")

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
