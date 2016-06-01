from pillarsdk import Node
from pillarsdk import Project
from pillarsdk.exceptions import ResourceNotFound
from flask import abort
from flask import render_template
from flask import redirect
from flask import request
from flask.ext.login import current_user
from werkzeug.contrib.atom import AtomFeed

from application import app
from application import SystemUtility
from application import cache
from application.modules.nodes import url_for_node
from application.modules.nodes.custom.posts import posts_view
from application.modules.nodes.custom.posts import posts_create
from application.helpers import attach_project_pictures
from application.helpers import current_user_is_authenticated
from application.helpers import get_file


@app.route("/")
@cache.cached(timeout=3600, unless=current_user_is_authenticated)
def homepage():
    """Homepage"""

    if not current_user.is_authenticated():
        return render_template(
            'join.html',
            title="join")

    # Get latest blog posts
    api = SystemUtility.attract_api()
    latest_posts = Node.all({
        'projection': {'name': 1, 'project': 1, 'user': 1, 'node_type': 1,
                       'picture': 1, 'properties.status': 1, 'properties.url': 1},
        'where': {'node_type': 'post', 'properties.status': 'published'},
        'embedded': {'user': 1, 'project': 1},
        'sort': '-_created',
        'max_results': '3'
        }, api=api)

    # Append picture Files to last_posts
    for post in latest_posts._items:
        if post.picture:
            post.picture = get_file(post.picture, api=api)

    # Get latest assets added to any project
    latest_assets = Node.latest('assets', api=api)

    # Append picture Files to latest_assets
    for asset in latest_assets._items:
        if asset.picture:
            asset.picture = get_file(asset.picture, api=api)

    # Get latest comments to any node
    latest_comments = Node.latest('comments', api=api)

    # Parse results for replies
    for comment in latest_comments._items:
        if comment.properties.is_reply:
            comment.parent = Node.find(comment.parent.parent, api=api)
        else:
            comment.parent = comment.parent

    main_project = Project.find(app.config['MAIN_PROJECT_ID'], api=api)
    main_project.picture_square = get_file(main_project.picture_square, api=api)
    main_project.picture_header = get_file(main_project.picture_header, api=api)

    return render_template(
        'homepage.html',
        main_project=main_project,
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


@app.errorhandler(403)
def error_404(e):
    return render_template('errors/403_embed.html'), 403


@app.route("/join")
@cache.cached(timeout=3600, unless=current_user_is_authenticated)
def join():
    """Join page"""
    return redirect("https://store.blender.org/product/membership/")


@app.route("/services")
def services():
    """Services page"""
    return render_template(
        'services.html',
        title="services")


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


@app.route("/p/<project_url>/blog/")
@app.route("/p/<project_url>/blog/<url>")
@cache.memoize(timeout=3600, unless=current_user_is_authenticated)
def project_blog(project_url, url=None):
    """View project blog"""
    api = SystemUtility.attract_api()
    try:
        project = Project.find_one({
            'where': '{"url" : "%s"}' % (project_url)}, api=api)
        return posts_view(project._id, url=url)
    except ResourceNotFound:
        return abort(404)


def get_projects(category):
    """Utility to get projects based on category. Should be moved on the API
    and improved with more extensive filtering capabilities.
    """
    api = SystemUtility.attract_api()
    projects = Project.all({
        'where': {
            'category': category,
            'is_private': False},
        'sort': '-_created',
        }, api=api)
    for project in projects._items:
        attach_project_pictures(project, api)
    return projects


@app.route("/open-projects")
@cache.cached(timeout=3600, unless=current_user_is_authenticated)
def open_projects():
    projects = get_projects('film')
    return render_template(
        'projects/index_collection.html',
        title='open-projects',
        projects=projects._items,
        api=SystemUtility.attract_api())


@app.route("/training")
@cache.cached(timeout=3600, unless=current_user_is_authenticated)
def training():
    projects = get_projects('training')
    return render_template(
        'projects/index_collection.html',
        title='training',
        projects=projects._items,
        api=SystemUtility.attract_api())


@app.route("/gallery")
def gallery():
    return redirect('/p/gallery')


@app.route("/textures")
def redir_textures():
    return redirect('/p/textures')


@app.route("/caminandes")
def caminandes():
    return redirect('/p/caminandes-3')


@app.route("/cf2")
def cf2():
    return redirect('/p/creature-factory-2')


@app.route("/characters")
def redir_characters():
    return redirect('/p/characters')


@app.route("/403")
def error_403():
    """Custom entry point to display the not allowed template"""
    return render_template('errors/403_embed.html')


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
    latest_posts = Node.all({
        'where': {'node_type': 'post', 'properties.status': 'published'},
        'embedded': {'user': 1},
        'sort': '-_created',
        'max_results': '15'
        }, api=api)

    # Populate the feed
    for post in latest_posts._items:
        author = post.user.fullname
        updated = post._updated if post._updated else post._created
        url = url_for_node(node=post)
        content = post.properties.content[:500]
        content = u'<p>{0}... <a href="{1}">Read more</a></p>'.format(content, url)
        feed.add(post.name, unicode(content),
                 content_type='html',
                 author=author,
                 url=url,
                 updated=updated,
                 published=post._created)
    return feed.get_response()

