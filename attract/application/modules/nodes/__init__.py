from attractsdk import Node
from attractsdk import NodeType
from attractsdk import User
from attractsdk import File
# from attractsdk import binaryFile
from attractsdk.exceptions import ResourceNotFound
from attractsdk.exceptions import ForbiddenAccess

from flask import abort
from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import flash
from flask import url_for
from flask import request
from flask import jsonify

from datetime import datetime

from application.modules.nodes.forms import get_node_form
from application.modules.nodes.forms import get_comment_form
from application.modules.nodes.forms import process_node_form
from application.helpers import Pagination

from application import app
from application import SystemUtility

from flask.ext.login import login_required
from flask.ext.login import current_user

from jinja2.exceptions import TemplateNotFound


RFC1123_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'


# Name of the Blueprint
nodes = Blueprint('nodes', __name__)

def type_names():
    api = SystemUtility.attract_api()

    types = NodeType.all(api=api)['_items']
    type_names = []
    for names in types:
        type_names.append(str(names['name']))
    return type_names

def assigned_users_to(node, node_type):
    api = SystemUtility.attract_api()

    if node_type['name'] != "task":
        return []
    users = node['properties']['owners']['users']
    owners = []
    for user in users:
        user_node = User.find(user, api=api)
        owners.append(user_node)
    return owners

@nodes.route("/<node_type_name>")
@login_required
def index(node_type_name=""):
    """Generic function to list all nodes
    """
    # Pagination index
    page = request.args.get('page', 1)
    max_results = 50

    api = SystemUtility.attract_api()
    if node_type_name == "":
        node_type_name = "shot"

    node_type_list = NodeType.all({
        'where': '{"name" : "%s"}' % node_type_name,
        }, api=api)

    if len(node_type_list['_items']) == 0:
        return "Empty NodeType list", 200

    node_type = node_type_list['_items'][0]


    nodes = Node.all({
        'where': '{"node_type" : "%s"}' % (node_type['_id']),
        'max_results': max_results,
        'page': page,
        'embedded': '{"picture":1}',
        'sort' : "order"}, api=api)

    # Build the pagination object
    pagination = Pagination(int(page), max_results, nodes._meta.total)

    template = '{0}/index.html'.format(node_type_name)

    return render_template(
        template,
        title=node_type_name,
        nodes=nodes,
        node_type=node_type,
        type_names=type_names(),
        pagination=pagination)


# XXX Hack to get custom data for DataTables for shot view
@nodes.route("/shots/index.json")
@login_required
def shots_index():
    max_results = 100

    api = SystemUtility.attract_api()
    node_type_name = "shot"
    node_type_list = NodeType.all({
        'where': '{"name" : "%s"}' % node_type_name,
        }, api=api)

    node_type = node_type_list._items[0]

    nodes = Node.all({
        'where': '{"node_type" : "%s"}' % node_type._id,
        'max_results': max_results,
        'embedded': '{"picture":1}',
        'sort' : "order"}, api=api)

    # Get the task node type object id
    node_type_list = NodeType.all({
        'where': '{"name" : "task"}',
        }, api=api)
    node_type_task = node_type_list._items[0]

    nodes_datatables = []
    for node in nodes._items:
        tasks = Node.all({
            'where': '{"node_type" : "%s", "parent" : "%s"}'\
                    % (node_type_task._id, node._id),
            'sort' : "order"}, api=api)

        #: shot name, Animation, Lighting, Simulation
        data = {
            'DT_RowId': "row_{0}".format(node._id),
            '_id': node._id,
            'order': node.order,
            'picture': None,
            'name': node.name,
            'description': node.description,
            'url_view': url_for('nodes.view', node_id=node._id),
            'url_edit': url_for('nodes.edit', node_id=node._id, embed=1),
            'tasks': {
                'animation': None,
                'lighting': None,
                'fx_hair': None,
                'fx_grass': None,
                'fx_smoke': None
                },
            }

        if node.picture:
            # This is an address on the Attract server, so it should be built
            # entirely here
            data['picture'] = "{0}/file_server/file/{1}".format(
                app.config['ATTRACT_SERVER_ENDPOINT'], node.picture.path)
            # Get previews
            picture_node = File.find(node.picture['_id'] + \
                                    '/?embedded={"previews":1}', api=api)

            if picture_node.previews:
                for preview in picture_node.previews:
                    if preview.size == 'm':
                        data['picture_thumbnail'] = app.config['ATTRACT_SERVER_ENDPOINT'] + "/file_server/file/" + preview.path
                        break
            else:
                data['picture_thumbnail'] = data['picture']


        if node.order is None:
            data['order'] = 0

        for task in tasks._items:
            # If there are tasks assigned to the shot we loop through them and
            # match them with the existing data indexes.
            if task.name in data['tasks']:
                data['tasks'][task.name] = {
                'name': task.name,
                'status': task.properties.status,
                'url_view': url_for('nodes.view', node_id=task._id, embed=1),
                'url_edit': url_for('nodes.edit', node_id=task._id, embed=1),
                'is_conflicting': task.properties.is_conflicting,
                'is_processing': task.properties.is_rendering,
                'is_open': task.properties.is_open
                }


        nodes_datatables.append(data)

    return jsonify(data=nodes_datatables)


# XXX Hack to get custom data
@nodes.route("/shots/<shot_id>.json")
@login_required
def shots_view(shot_id):
    return jsonify(_id=shot_id)


@nodes.route("/<node_id>/view", methods=['GET', 'POST'])
@login_required
def view(node_id):
    api = SystemUtility.attract_api()
    # Get node with embedded picture data
    try:
        node = Node.find(node_id + '/?embedded={"picture":1}', api=api)
    except ResourceNotFound:
        node = None
    user_id = current_user.objectid
    if node:
        # Get comment type
        comment_type = NodeType.all({'where': '{"name" : "comment"}'}, api=api)
        comment_type = comment_type['_items'][0]
        # Get node type
        node_type = NodeType.find(node['node_type'], api=api)
        # Get comments form
        comment_form = get_comment_form(node, comment_type)
        if comment_form.validate_on_submit():
            if process_node_form(comment_form,
                                    node_id=None,
                                    node_type=comment_type,
                                    user=user_id):
                node = Node.find(node_id + '/?embedded={"picture":1}', api=api)
            else:
                print (comment_form.errors)
        # Get previews
        if node.picture:
            picture_node = File.find(node.picture['_id'] + \
                                    '/?embedded={"previews":1}', api=api)
            node['picture'] = "{0}{1}".format(SystemUtility.attract_server_endpoint_static(), picture_node.path)
            if picture_node.previews:
                for preview in picture_node.previews:
                    if preview.size == 'l':
                        node['picture_thumbnail'] = "{0}{1}".format(SystemUtility.attract_server_endpoint_static(), preview.path)
                        break
            else:
                node['picture_thumbnail'] = node['picture']
        # Get Parent
        try:
            parent = Node.find(node['parent'], api=api)
        except KeyError:
            parent = None
        except ResourceNotFound:
            parent = None
        # Get children
        children = Node.all({
            'where': '{"parent": "%s"}' % node['_id'],
            'embedded': '{"picture": 1, "user": 1}'}, api=api)

        children = children.to_dict()['_items']
        # TODO this logic should be on Server:
        AllNodeTypes = NodeType.all(api=api)
        for child in children:
            for ntype in AllNodeTypes['_items']:
                if child['node_type'] == ntype['_id']:
                    child['node_type_name'] = ntype['name']
                    break
        # Get Comments
        comments = []
        for child in children:
            if child['node_type'] == comment_type['_id']:
                comments.append(child)

        # Get comment attachments
        for comment in comments:
            comment['attachments'] = []
            for attachment in comment['properties']['attachments']:
                try:
                    attachment_file = File.find(attachment, api=api)
                except ResourceNotFound:
                    attachment_file = None
                comment['attachments'].append(attachment_file)

        # Get assigned users
        assigned_users = assigned_users_to(node, node_type)

        if request.args.get('format'):
            if request.args.get('format') == 'json':
                node = node.to_dict()
                node['url_edit'] = url_for('nodes.edit', node_id=node['_id']),
                if parent:
                    parent = parent.to_dict()
                return_content = jsonify({
                    'node': node,
                    'children': children,
                    'parent': parent
                })
        else:
            embed_string = ''
            # Check if we want to embed the content via an AJAX call
            if request.args.get('embed'):
                if request.args.get('embed') == '1':
                    # Define the prefix for the embedded template
                    embed_string = '_embed'
            return_content = render_template(
            '{0}/view{1}.html'.format(node_type['name'], embed_string),
            node=node,
            type_names=type_names(),
            parent=parent,
            children=children,
            comments=comments,
            comment_form=comment_form,
            assigned_users=assigned_users,
            config=app.config)

        return return_content
    else:
        return abort(404)


@nodes.route("/<node_type_id>/add", methods=['GET', 'POST'])
@login_required
def add(node_type_id):
    """Generic function to add a node of any type
    """
    api = SystemUtility.attract_api()
    ntype = NodeType.find(node_type_id, api=api)
    form = get_node_form(ntype)
    user_id = current_user.objectid
    if form.validate_on_submit():
        if process_node_form(form, node_type=ntype, user=user_id):
            flash('Node correctly added')
            return redirect(url_for('nodes.index', node_type_name=ntype['name']))
    else:
        print form.errors
    return render_template('nodes/add.html',
        node_type=ntype,
        form=form,
        errors=form.errors,
        type_names=type_names())


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


# XXX Hack to edit tasks via AJAX
@nodes.route("/shots/edit", methods=['POST'])
@login_required
def shot_edit():
    """We want to be able to edit the following properties:
    - notes
    - status
    - cut in
    - cut out
    - picture (optional)
    """
    api = SystemUtility.attract_api()
    shot_id = request.form['shot_id']

    shot = Node.find(shot_id, api=api)
    shot.properties.notes = request.form['shot_notes']
    shot.properties.status = request.form['shot_status']
    shot.properties.cut_in = int(request.form['shot_cut_in'])
    shot.properties.cut_out = int(request.form['shot_cut_out'])

    shot.update(api=api)

    return jsonify(shot.to_dict())


@nodes.route("/<node_id>/edit", methods=['GET', 'POST'])
@login_required
def edit(node_id):
    """Generic node editing form
    """
    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)
    node_type = NodeType.find(node.node_type, api=api)
    form = get_node_form(node_type)
    user_id = current_user.objectid
    node_schema = node_type['dyn_schema'].to_dict()
    form_schema = node_type['form_schema'].to_dict()
    error = ""

    if form.validate_on_submit():
        if process_node_form(
                form, node_id=node_id, node_type=node_type, user=user_id):
            node = Node.find(node_id, api=api)
            flash ('Node "{0}" correctly edited'.format(node.name))
            return redirect(url_for('nodes.index', node_type_name=node_type['name']))
        else:
            error = "Server error"
            print ("Error sending data")
    else:
        print form.errors

    # Populate Form
    form.name.data = node.name
    form.description.data = node.description
    if 'picture' in form:
        form.picture.data = node.picture
    if node.parent:
        form.parent.data = node.parent

    def set_properties(
            node_schema, form_schema, prop_dict, form, prefix=""):
        for prop in node_schema:
            if not prop in prop_dict:
                continue
            schema_prop = node_schema[prop]
            form_prop = form_schema[prop]
            prop_name = "{0}{1}".format(prefix, prop)
            if schema_prop['type'] == 'dict':
                set_properties(
                    schema_prop['schema'],
                    form_prop['schema'],
                    prop_dict[prop_name],
                    form,
                    "{0}__".format(prop_name))
            else:
                try:
                    data = prop_dict[prop]
                except KeyError:
                    print ("{0} not found in form".format(prop_name))
                if schema_prop['type'] == 'datetime':
                    data = datetime.strptime(data, RFC1123_DATE_FORMAT)
                if prop_name in form:
                    form[prop_name].data = data


    prop_dict = node.properties.to_dict()
    set_properties(node_schema, form_schema, prop_dict, form)


    # Get Parent
    try:
        parent = Node.find(node['parent'], api=api)
    except KeyError:
        parent = None
    except ResourceNotFound:
        parent = None

    embed_string = ''
    # Check if we want to embed the content via an AJAX call
    if request.args.get('embed'):
        if request.args.get('embed') == '1':
            # Define the prefix for the embedded template
            embed_string = '_embed'

    template = '{0}/edit{1}.html'.format(node_type['name'], embed_string)

    # We should more simply check if the template file actually exsists on
    # the filesystem level
    try:
        return render_template(
                template,
                node=node,
                parent=parent,
                form=form,
                errors=form.errors,
                error=error)
    except TemplateNotFound:
        template = 'nodes/edit{1}.html'.format(node_type['name'], embed_string)
        return render_template(
                template,
                node=node,
                parent=parent,
                form=form,
                errors=form.errors,
                error=error)


@nodes.route("/<node_id>/delete", methods=['GET', 'POST'])
@login_required
def delete(node_id):
    """Generic node deletion
    """
    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)
    name = node.name
    node_type = NodeType.find(node.node_type, api=api)
    try:
        node.delete(api=api)
        forbidden = False
    except ForbiddenAccess:
        forbidden = True

    if not forbidden:
        flash('Node "{0}" correctly deleted'.format(name))
        # print (node_type['name'])
        return redirect(url_for('nodes.index', node_type_name=node_type['name']))
    else:
        flash('Forbidden access')
        return redirect(url_for('nodes.edit', node_id=node._id))
