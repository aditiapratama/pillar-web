from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk import File
from pillarsdk.exceptions import ResourceNotFound
from flask import abort
from flask import render_template
from flask import redirect
from flask import url_for
from flask.ext.login import login_required
from flask.ext.login import current_user
from application import app
from application import SystemUtility
from application.modules.nodes import nodes
from application.modules.nodes.forms import get_node_form
from application.modules.nodes.forms import process_node_form

def posts_view(project_id, url=None):
    """View individual blogpost"""
    api = SystemUtility.attract_api()
    # Fetch project (for backgroud images and links generation)
    project = Node.find(project_id, api=api)
    if project.properties.picture_square:
        picture_square = File.find(project.properties.picture_square, api=api)
        project.properties.picture_square = picture_square
    if project.properties.picture_header:
        picture_header = File.find(project.properties.picture_header, api=api)
        project.properties.picture_header = picture_header

    node_type = NodeType.find_one({
        'where': '{"name" : "blog"}',
        'projection': '{"name": 1, "permissions":1}'
        }, api=api)
    blog = Node.find_one({
        'where': '{"node_type" : "%s", \
            "parent": "%s"}' % (node_type._id, project_id),
        }, api=api)
    if url:
        try:
            post = Node.find_one({
                'where': '{"parent": "%s", "properties.url": "%s"}' % (blog._id, url),
                'embedded': '{"picture":1, "node_type": 1, "user": 1}',
                }, api=api)
        except ResourceNotFound:
            return abort(404)

        return render_template(
            'nodes/custom/post/view.html',
            blog=blog,
            node=post,
            project=project)
    else:
        # Render all posts
        node_type_post = NodeType.find_one({
            'where': '{"name" : "post"}',
            'projection': '{"permissions":1}'
            }, api=api)

        posts = Node.all({
            'where': '{"parent": "%s"}' % (blog._id),
            'embedded': '{"picture":1, "user": 1}',
            'sort': '-_created'
            }, api=api)
        return render_template(
            'nodes/custom/blog/index.html',
            node_type_post=node_type_post,
            posts=posts._items,
            project=project)


@nodes.route("/posts/<project_id>/create", methods=['GET', 'POST'])
@login_required
def posts_create(project_id):
    api = SystemUtility.attract_api()
    node_type = NodeType.find_one({
        'where': '{"name" : "blog"}',
        'projection': '{"name": 1, "permissions": 1}'
        }, api=api)
    blog = Node.find_first({
        'where': '{"node_type" : "%s", \
            "parent": "%s"}' % (node_type._id, project_id),
        }, api=api)
    node_type = NodeType.find_one({'where': '{"name" : "post"}',}, api=api)
    form = get_node_form(node_type)
    if form.validate_on_submit():
        user_id = current_user.objectid
        if process_node_form(
                form, node_type=node_type, user=user_id):
            return redirect(url_for('main_blog'))
    form.parent.data = blog._id
    return render_template('nodes/custom/post/create.html',
        node_type=node_type,
        form=form,
        project_id=project_id)
