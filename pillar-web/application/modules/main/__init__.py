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
from flask import request
from flask import url_for
from flask.ext.login import login_required
from flask.ext.login import current_user
from werkzeug.contrib.atom import AtomFeed
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
from application.helpers import get_file

@app.route("/")
@cache.cached(timeout=3600, unless=current_user_is_authenticated)
def homepage():
    """Homepage"""

    # Get latest blog posts
    api = SystemUtility.attract_api()
    node_type_post = NodeType.find_one({
        'where': '{"name" : "post"}',
        'projection': '{"permissions": 1}'
        }, api=api)
    latest_posts = Node.all({
        'projection': '{"name":1, "project": 1, "user":1, "node_type":1, \
            "picture": 1, "properties.status": 1}',
        'where': '{"node_type": "%s", "properties.status": "published"}' % (node_type_post._id),
        'embedded': '{"user": 1, "project":1}',
        'sort': '-_created',
        'max_results': '3'
        }, api=api)

    # Append picture Files to latst_posts
    for post in latest_posts._items:
        if post.picture:
            post.picture = get_file(post.picture)

    # Get latest assets added to any project
    node_type_asset = NodeType.find_one({
        'where': '{"name" : "asset"}',
        'projection': '{"permissions": 1}'
        }, api=api)
    latest_assets = Node.all({
        'projection': '{"name":1, "project": 1, "user":1, "node_type":1, \
            "picture": 1, "properties.status": 1}',
        'where': '{"node_type": "%s", "properties.status": "published"}' % (node_type_asset._id),
        'embedded': '{"user":1}',
        'sort': '-_created',
        'max_results': '12'
        }, api=api)

    # Append picture Files to latest_assets
    for asset in latest_assets._items:
        if asset.picture:
            asset.picture = get_file(asset.picture)

    # Get latest comments to any node
    node_type_comment = NodeType.find_one({
        'where': '{"name" : "comment"}',
        'projection': '{"permissions": 1}'
        }, api=api)
    latest_comments = Node.all({
        'projection': '{"project": 1, "parent": 1, "user": 1, \
            "properties.content": 1 ,"node_type": 1, "properties.status": 1}',
        'where': '{"node_type": "%s", "properties.status": "published"}' % (node_type_comment._id),
        'embedded': '{"user": 1, "project": 1, "parent": 1}',
        'sort': '-_created',
        'max_results': '6'
        }, api=api)

    # Parse results for replies
    for comment in latest_comments._items:
        if comment.properties.is_reply:
            comment.parent = comment.parent.parent
        else:
            comment.parent = comment.parent._id

    return render_template(
        'homepage.html',
        latest_posts=latest_posts._items,
        latest_assets=latest_assets._items,
        latest_comments=latest_comments._items,
        api=api)


@app.errorhandler(500)
def error_500(e):
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def error_404(e):
    return render_template('errors/404.html'), 404


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


@app.route("/p/<project_url>/blog/")
@app.route("/p/<project_url>/blog/<url>")
@cache.memoize(timeout=3600, unless=current_user_is_authenticated)
def project_blog(project_url, url=None):
    """View project blog"""
    api = SystemUtility.attract_api()
    try:
        project = Node.find_one({
            'where': '{"properties.url" : "%s"}' % (project_url)}, api=api)
        session['current_project_id'] = project._id
        return posts_view(project._id, url=url)
    except ResourceNotFound:
        return abort(404)


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
        'sort': '-_created'
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


@app.route("/gallery")
def gallery():
    return redirect('/p/gallery')


@app.route("/caminandes")
def caminandes():
    return redirect('/p/caminandes-3')

# Shameful redirects
@app.route("/p/blender-cloud/")
def redirect_cloud_blog():
    return redirect('/blog')


@app.route('/feeds/blogs.atom')
@cache.cached(60*5)
def feeds_blogs():
    """Global feed generator for latest blogposts across all projects"""
    feed = AtomFeed('Blender Cloud - Latest updates',
                    feed_url=request.url, url=request.url_root)
    # Get latest blog posts
    api = SystemUtility.attract_api()
    node_type_post = NodeType.find_one({
        'where': '{"name" : "post"}',
        'projection': '{"permissions": 1}'
        }, api=api)
    latest_posts = Node.all({
        'where': '{"node_type": "%s", "properties.status": "published"}' % (node_type_post._id),
        'embedded': '{"user": 1, "project":1}',
        'sort': '-_created',
        'max_results': '15'
        }, api=api)

    # Populate the feed
    for post in latest_posts._items:
        author = post.user.fullname
        updated = post._updated if post._updated else post._created
        url = url_for('nodes.view', node_id=post._id, redir=1, _external=True)
        content = post.properties.content[:500]
        content = u'<p>{0}... <a href="{1}">Read more</a></p>'.format(content, url)
        feed.add(post.name, unicode(content),
                 content_type='html',
                 author=author,
                 url=url,
                 updated=updated,
                 published=post._created)
    return feed.get_response()

