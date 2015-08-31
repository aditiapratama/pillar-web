from attractsdk import Node
from attractsdk import NodeType
from attractsdk import User
from attractsdk import File
from attractsdk.exceptions import ResourceNotFound
from attractsdk.exceptions import ForbiddenAccess

from flask import url_for
from flask import jsonify

from flask.ext.login import login_required
from flask.ext.login import current_user

from application import app
from application import SystemUtility
from application.modules.nodes import nodes

# XXX Hack to create a task with a single click
@nodes.route("/tasks/add", methods=['POST'])
@login_required
def task_add():
    api = SystemUtility.attract_api()
    shot_id = request.form['shot_id']
    task_name = request.form['task_name']

    node_type_list = NodeType.all({
        'where': "name=='task'",
        }, api=api)
    node_type = node_type_list['_items'][0]

    node_type_id = node_type._id
    import datetime

    RFC1123_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
    node = Node()
    prop = {}
    prop['node_type'] = node_type_id
    prop['name'] = task_name
    prop['description'] = ''
    prop['user'] = current_user.objectid
    prop['parent'] = shot_id
    prop['properties'] = {
        'status': 'todo',
        'owners': {
            'users': [],
            'groups': []},
        'time': {
            'duration': 10,
            'start': datetime.datetime.strftime(datetime.datetime.now(), '%a, %d %b %Y %H:%M:%S GMT')}
        }
    post = node.post(prop, api=api)
    return jsonify(node.to_dict())


# XXX Hack to edit tasks via AJAX
@nodes.route("/tasks/edit", methods=['POST'])
@login_required
def task_edit():
    """We want to be able to edit the following properties:
    - status
    - owners
    - description
    - picture (optional)
    """
    api = SystemUtility.attract_api()
    task_id = request.form['task_id']

    task = Node.find(task_id, api=api)
    task.description = request.form['task_description']
    if request.form['task_revision']:
        task.properties.revision = int(request.form['task_revision'])
    task.properties.status = request.form['task_status']
    task.properties.filepath = request.form['task_filepath']
    task.properties.owners.users = request.form.getlist('task_owners_users[]')

    siblings = Node.all({
        'where': 'parent==ObjectId("%s")' % task.parent,
        'embedded': '{"picture":1, "user":1}'}, api=api)

    def check_conflict(task_current, task_sibling):
        return revsion_conflict[task_current.name](task_current, task_sibling)

    def task_animation(task_current, task_sibling):
        if task_sibling.name in ['fx_hair', 'fx_smoke', 'fx_grass', 'lighting']:
            if task_current.properties.revision > task_sibling.properties.revision:
                return True
        return False

    def task_lighting(task_current, task_sibling):
        if task_sibling.name in ['fx_hair', 'fx_smoke', 'fx_grass', 'animation']:
            if task_current.properties.revision < task_sibling.properties.revision:
                return True
        return False

    def task_fx_hair(task_current, task_sibling):
        if task_sibling.name in ['animation']:
            if task_current.properties.revision < task_sibling.properties.revision:
                return True
        if task_sibling.name in ['lighting']:
            if task_current.properties.revision > task_sibling.properties.revision:
                return True
        return False


    def task_fx_grass(task_current, task_sibling):
        pass

    def task_fx_smoke(task_current, task_sibling):
        pass

    revsion_conflict = {
        'animation': task_animation,
        'lighting': task_lighting,
        'fx_hair': task_fx_hair,
        'fx_grass': task_fx_grass,
        'fx_smoke': task_fx_smoke
    }

    if task.properties.revision:
        for sibling in siblings._items:
            if sibling.properties.revision and sibling._id != task_id:
                if check_conflict(task, sibling) == True:
                    task.properties.is_conflicting = True
                    break
                else:
                    task.properties.is_conflicting = False

    task.update(api=api)

    return jsonify(task.to_dict())

