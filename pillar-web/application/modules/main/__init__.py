from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk.users import User
from pillarsdk import File
from pillarsdk.organizations import Organization
from pillarsdk.exceptions import ResourceNotFound
from flask import abort
from flask import render_template
from flask import session
from flask import redirect
from flask.ext.login import login_required
from flask.ext.login import current_user
from application import app
from application import SystemUtility
from application import cache
from application.modules.nodes import index
from application.modules.nodes import view
from application.modules.nodes.custom.posts import posts_view
from application.modules.nodes.custom.posts import posts_create
from application.modules.users.model import UserProxy
from application.helpers import attach_project_pictures
from application.helpers import current_user_is_authenticated

@app.route("/")
@cache.cached(timeout=3600, unless=current_user_is_authenticated)
def homepage():
    """Homepage"""
    if current_user.is_authenticated():
        api = SystemUtility.attract_api()
        node_type_post = NodeType.find_one({
            'where': '{"name" : "post"}',
            'projection': '{"permissions": 1}'
            }, api=api)
        latest_posts = Node.all({
            'where': '{"node_type": "%s", "properties.status": "published"}' % (node_type_post._id),
            'embedded': '{"picture":1, "project":1}',
            'sort': '-_created',
            'max_results': '5'
            }, api=api)

        node_type_asset = NodeType.find_one({
            'where': '{"name" : "asset"}',
            'projection': '{"permissions": 1}'
            }, api=api)
        latest_assets = Node.all({
            'where': '{"node_type": "%s", "properties.status": "published"}' % (node_type_asset._id),
            'embedded': '{"picture":1, "user":1}',
            'sort': '-_created',
            'max_results': '5'
            }, api=api)

        return render_template(
            'homepage.html',
            latest_posts=latest_posts._items,
            latest_assets=latest_assets._items)
    else:
        return render_template(
            'homepage.html')


@app.route("/join")
@cache.cached(timeout=3600, unless=current_user_is_authenticated)
def join():
    """Join page"""
    return redirect("https://store.blender.org/product/membership/")
    return render_template(
        'join.html')


# @app.route("/stats")
# def stats():
#     """Stats page"""
#     return render_template(
#         'stats.html')


@app.route("/blog/")
@app.route("/blog/<url>")
@cache.memoize(timeout=3600, unless=current_user_is_authenticated)
def main_blog(url=None):
    """Blog with project news"""
    project_id = app.config['MAIN_PROJECT_ID']
    return posts_view(project_id, url)


@app.route("/blog/create")
def main_posts_create():
    project_id = app.config['MAIN_PROJECT_ID']
    return posts_create(project_id)

@app.route("/<name>/")
@cache.memoize(timeout=3600, unless=current_user_is_authenticated)
def user_view(name):
    """View a user or organization."""
    user = UserProxy(name)
    projects = user.projects()
    return render_template(
        'nodes/custom/project/index_collection.html',
        user=user,
        projects=projects._items)


@app.route("/<name>/<project>/blog/")
@app.route("/<name>/<project>/blog/<url>")
@cache.memoize(timeout=3600, unless=current_user_is_authenticated)
def project_blog(name, project, url=None):
    """View project blog"""
    user = UserProxy(name)
    project = user.project(project)
    session['current_project_id'] = project._id
    return posts_view(project._id, url=url)


# @app.route("/<name>/<project>/<node_id>")
# def node_view(name, project, node_id):
#     """Entry point to view a project.
#     """
#     user = UserProxy(name)
#     project = user.project(project)
#     api = SystemUtility.attract_api()
#     try:
#         node = Node.find(node_id + '/?embedded={"picture":1,"node_type":1}', api=api)
#     except ResourceNotFound:
#         return abort(404)
#     return node.name


def get_projects(category):
    """Utility to get projects based on category. Should be moved on the API
    and improved with more extensive filtering capabilities.
    """
    api = SystemUtility.attract_api()
    node_type = NodeType.find_one({
        'where': '{"name" : "project"}',
        'projection': '{"name": 1, "permissions": 1}'
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
@cache.cached(timeout=3600, unless=current_user_is_authenticated)
def open_projects():
    projects = get_projects('film')
    return render_template(
        'nodes/custom/project/index_collection.html',
        title='open-projects',
        projects=projects._items,
        api=SystemUtility.attract_api())


@app.route("/training")
@cache.cached(timeout=3600, unless=current_user_is_authenticated)
def training():
    projects = get_projects('training')
    return render_template(
        'nodes/custom/project/index_collection.html',
        title='training',
        projects=projects._items,
        api=SystemUtility.attract_api())
