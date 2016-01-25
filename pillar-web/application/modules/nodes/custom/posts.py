from pillarsdk import Node
from pillarsdk import Project
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
from application.helpers import attach_project_pictures
from application.helpers import get_file
from application.modules.nodes import nodes
from application.modules.nodes.forms import get_node_form
from application.modules.nodes.forms import process_node_form
from application.modules.projects import project_update_nodes_list

def posts_view(project_id, url=None):
    """View individual blogpost"""
    api = SystemUtility.attract_api()
    # Fetch project (for backgroud images and links generation)
    project = Project.find(project_id, api=api)
    attach_project_pictures(project, api)

    blog = Node.find_one({
        'where': '{"node_type" : "blog", \
            "project": "%s"}' % (project_id),
        }, api=api)
    if url:
        try:
            post = Node.find_one({
                'where': '{"parent": "%s", "properties.url": "%s"}' % (blog._id, url),
                'embedded': '{"node_type": 1, "user": 1}',
                }, api=api)
            if post.picture:
                post.picture = get_file(post.picture)
        except ResourceNotFound:
            return abort(404)

        # If post is not published, check that the user is also the author of
        # the post. If not, return 404.
        if post.properties.status != "published":
            if current_user.is_authenticated():
                if not post.has_method('PUT'):
                    abort(403)
            else:
                abort(403)

        return render_template(
            'nodes/custom/post/view.html',
            blog=blog,
            node=post,
            project=project,
            api=api)
    else:
        node_type_post = project.get_node_type('post')
        print node_type_post

        status_query = "" if blog.has_method('PUT') else ', "properties.status": "published"'
        posts = Node.all({
            'where': '{"parent": "%s" %s}' % (blog._id, status_query),
            'embedded': '{"user": 1}',
            'sort': '-_created'
            }, api=api)
        return render_template(
            'nodes/custom/blog/index.html',
            node_type_post=node_type_post,
            posts=posts._items,
            project=project,
            api=api)


@nodes.route("/posts/<project_id>/create", methods=['GET', 'POST'])
@login_required
def posts_create(project_id):
    api = SystemUtility.attract_api()
    try:
        project = Node.find(project_id, api=api)
    except ResourceNotFound:
        return abort(404)
    attach_project_pictures(project, api)

    node_type = NodeType.find_one({
        'where': '{"name" : "blog"}',
        'projection': '{"name": 1, "permissions": 1}'
        }, api=api)
    blog = Node.find_first({
        'where': '{"node_type" : "%s", \
            "parent": "%s"}' % (node_type._id, project_id),
        }, api=api)
    node_type = NodeType.find_one({'where': '{"name" : "post"}',}, api=api)
    # Check if user is allowed to create a post in the blog
    if not node_type.has_method('POST'):
        return abort(403)
    form = get_node_form(node_type)
    if form.validate_on_submit():
        # Create new post object from scratch
        post_props = dict(
            node_type=node_type._id,
            name=form.name.data,
            picture=form.picture.data,
            user=current_user.objectid,
            parent=blog._id,
            project=project._id,
            properties=dict(
                content=form.content.data,
                status=form.status.data,
                url=form.url.data))
        post = Node(post_props)
        post.create(api=api)
        # Only if the node is set as published, push it to the list
        if post.properties.status == 'published':
            project_update_nodes_list(post, project_id=project._id, list_name='blog')
        return redirect(url_for('nodes.view', node_id=post._id, redir=1))
    form.parent.data = blog._id
    return render_template('nodes/custom/post/create.html',
        node_type=node_type,
        form=form,
        project=project,
        api=api)


@nodes.route("/posts/<post_id>/edit", methods=['GET', 'POST'])
@login_required
def posts_edit(post_id):
    api = SystemUtility.attract_api()

    try:
        post = Node.find(post_id, {
            'embedded': '{"user": 1}'}, api=api)
        if post.picture:
            post.picture = File.find(post.picture, api=api)
        node_type = post.node_type
    except ResourceNotFound:
        return abort(404)
    # Check if user is allowed to edit the post
    if not post.has_method('PUT'):
        return abort(403)

    project = Project.find(post.project, api=api)
    attach_project_pictures(project, api)

    node_type = project.get_node_type(post.node_type)
    form = get_node_form(node_type)
    if form.validate_on_submit():
        if process_node_form(form, node_id=post_id, node_type=node_type,
                            user=current_user.objectid):
            # The the post is published, add it to the list
            if form.status.data == 'published':
                project_update_nodes_list(post, project_id=project._id, list_name='blog')
            return redirect(url_for('nodes.view', node_id=post._id, redir=1))
    form.parent.data = post.parent
    form.name.data = post.name
    form.content.data = post.properties.content
    form.status.data = post.properties.status
    form.url.data = post.properties.url
    if post.picture:
        form.picture.data = post.picture._id
    return render_template('nodes/custom/post/edit.html',
        node_type=node_type,
        post=post,
        form=form,
        project=project,
        api=api)

