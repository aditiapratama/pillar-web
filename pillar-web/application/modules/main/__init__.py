from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk.users import User
from pillarsdk import File
from pillarsdk.organizations import Organization
from pillarsdk.exceptions import ResourceNotFound
from flask import abort
from flask import render_template
from flask.ext.login import login_required
from flask.ext.login import current_user
from application import app
from application import SystemUtility
from application.modules.nodes import index
from application.modules.nodes import view
from application.modules.users.model import UserProxy
from application.helpers import attach_project_pictures


@app.route("/")
def homepage():
    """Homepage"""
    return render_template(
        'homepage.html')


@app.route("/join")
def join():
    """Join page"""
    return render_template(
        'join.html')


@app.route("/stats")
def stats():
    """Stats page"""
    return render_template(
        'stats.html')


@app.route("/<name>/")
def user_view(name):
    """View a user or organization."""
    user = UserProxy(name)
    projects = user.projects()
    return render_template(
        'project/index_collection.html',
        user=user,
        projects=projects._items)


@app.route("/<name>/<project>/")
def project_view(name, project):
    """Entry point to view a project.
    """
    user = UserProxy(name)
    project = user.project(project)
    return view(project._id)


@app.route("/<name>/<project>/<node_id>")
def node_view(name, project, node_id):
    """Entry point to view a project.
    """
    user = UserProxy(name)
    project = user.project(project)
    api = SystemUtility.attract_api()
    try:
        node = Node.find(node_id + '/?embedded={"picture":1,"node_type":1}', api=api)
    except ResourceNotFound:
        return abort(404)
    return node.name


def get_projects(category):
    """Utility to get projects based on category. Should be moved on the API
    and improved with more extensive filtering capabilities.
    """
    api = SystemUtility.attract_api()
    node_type = NodeType.find_first({
        'where': '{"name" : "project"}',
        'projection': '{"name": 1}'
        }, api=api)
    projects = Node.all({
        'where': '{"node_type" : "%s", \
            "properties.category": "%s"}' % (node_type._id, category),
        'embedded': '{"picture":1}',
        }, api=api)
    for project in projects._items:
        attach_project_pictures(project, api)
    return projects


@app.route("/open-projects")
def open_projects():
    projects = get_projects('film')
    return render_template(
        'project/index_collection.html',
        projects=projects._items)


@app.route("/training")
def training():
    projects = get_projects('training')
    return render_template(
        'project/index_collection.html',
        projects=projects._items)
