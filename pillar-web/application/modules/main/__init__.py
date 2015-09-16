from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk.users import User
from pillarsdk.organizations import Organization
from pillarsdk.exceptions import ResourceNotFound
from flask import abort
from flask.ext.login import login_required
from flask.ext.login import current_user
from application import app
from application import SystemUtility
from application.modules.nodes import index
from application.modules.nodes import view
from application.helpers import UserProxy


@app.route("/")
@login_required
def homepage():
    """Very minimal setup that returns the nodes index view"""
    return index()

@app.route("/<name>/")
def user_view(name):
    """View a user or organization."""
    user = UserProxy(name)
    return user.name

@app.route("/<name>/<project>/")
@login_required
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
