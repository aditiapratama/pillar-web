from pillarsdk import Node
from pillarsdk import NodeType
from pillarsdk.exceptions import ResourceNotFound
from flask import abort
from flask import render_template
from flask.ext.login import login_required
from flask.ext.login import current_user
from application import app
from application import SystemUtility
from application.modules.nodes import nodes
from application.modules.nodes.forms import get_node_form

def posts_view(project_id, url=None):
    """View individual blogpost"""
    api = SystemUtility.attract_api()
    node_type = NodeType.find_first({
        'where': '{"name" : "blog"}',
        'projection': '{"name": 1}'
        }, api=api)
    blog = Node.find_first({
        'where': '{"node_type" : "%s", \
            "parent": "%s"}' % (node_type._id, project_id),
        }, api=api)
    if url:
        try:
            post = Node.find_one({
                'where': '{"parent": "%s", "properties.url": "%s"}' % (blog._id, url),
                'embedded': '{"picture":1, "node_type": 1}',
                }, api=api)
        except ResourceNotFound:
            return abort(404)

        return render_template(
            'nodes/custom/post/view.html',
            node=post)
    else:
        # Render all posts
        posts = Node.all({
            'where': '{"parent": "%s"}' % (blog._id),
            'embedded': '{"picture":1}',
            }, api=api)
        return render_template(
            'nodes/custom/blog/index.html',
            posts=posts._items)


@nodes.route("/posts/<project>/create")
@login_required
def posts_create(project):
    api = SystemUtility.attract_api()
    node_type = NodeType.find_first({'where': '{"name" : "post"}',}, api=api)
    form = get_node_form(node_type)
    # if form.validate_on_submit():
    #     node_type.name = form.name.data
    #     node_type.description = form.description.data
    #     node_type.url = form.url.data
    #     # Processing custom fields
    #     for field in form.properties:
    #         print field.data['id']
    # else:
    #     print form.errors
    return render_template('nodes/add.html', node_type=node_type, form=form)
