from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk import User
from pillarsdk import File
from pillarsdk.exceptions import ResourceNotFound
from pillarsdk.exceptions import ForbiddenAccess

from flask import url_for
from flask import jsonify

from flask.ext.login import login_required
from flask.ext.login import current_user

from application import app
from application import SystemUtility
from application.modules.nodes import nodes

# Custom nodes view for DataTables
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

        shot_status = None

        try:
            shot_status = node.properties.status
        except:
            # Notify about missing status property. This should be prominent.
            pass

        data = {
            'DT_RowId': "row_{0}".format(node._id),
            'DT_RowAttr': {'data-shot-status':shot_status},
            '_id': node._id,
            'order': node.order,
            'picture': None,
            'name': node.name,
            #'description': node.description,
            'notes': node.properties.notes,
            'timing': {
                'cut_in': node.properties.cut_in,
                'cut_out': node.properties.cut_out
                },
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
