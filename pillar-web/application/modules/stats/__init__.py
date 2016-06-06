from pillarsdk import Node
from pillarsdk import NodeType

from flask import Blueprint
from flask import render_template

from application import system_util
from application.helpers import percentage

from flask.ext.login import login_required


# Name of the Blueprint
stats = Blueprint('stats', __name__)

# @stats.route("/")
# @login_required
# def index():
#     """Custom production stats entry point
#     """
#     api = system_util.attract_api()
#     node_type_list = NodeType.all(
#         {'where': '{"name": "%s"}' % ('shot')}, api=api)

#     node_type = node_type_list['_items'][0]
#     nodes = Node.all({
#         'where': '{"node_type": "%s"}' % (node_type['_id']),
#         'max_results': 100,
#         'sort' : "order"}, api=api)

#     node_statuses = {}

#     node_totals = {
#         'count': 0,
#         'frames': 0
#     }

#     for shot in nodes._items:
#         status = shot.properties.status
#         if status not in node_statuses:
#             # If they key does not exist, initialize with defaults
#             node_statuses[status] = {
#                 'count': 0,
#                 'frames': 0}

#         # Calculate shot duration and increase status count
#         frames = shot.properties.cut_out - shot.properties.cut_in
#         node_statuses[status]['count'] += 1
#         node_statuses[status]['frames'] += frames
#         # Update the global stats
#         node_totals['count'] += 1
#         node_totals['frames'] += frames

#     for node_status in node_statuses:
#         # Calculate completion percentage based on total duration
#         print node_statuses[node_status]['frames']
#         print node_totals['frames']
#         node_statuses[node_status]['completion'] = percentage(
#             node_statuses[node_status]['frames'], node_totals['frames'])

#     return render_template(
#         'stats/index.html',
#         node_statuses=node_statuses)
