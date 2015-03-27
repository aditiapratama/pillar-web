from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import render_template
from flask import redirect
from flask import request
from flask import flash
from flask import url_for

from attractsdk import Node
from attractsdk import NodeType

from application.modules.nodes.forms import NodeTypeForm
from application.modules.nodes.forms import CustomFieldForm
from application.modules.nodes.forms import get_node_form
from application.modules.nodes.forms import process_node_form


# Name of the Blueprint
nodes = Blueprint('nodes', __name__)


def type_names():
    types = NodeType.all()["_items"]
    type_names = []
    for names in types:
        type_names.append(str(names['name']))
    return type_names


@nodes.route("/<node_name>", methods=['GET', 'POST'])
def index(node_name=""):
    """Generic function to list all nodes
    """
    nodes = Node.all()
    nodes = nodes['_items']
    if node_name=="":
        node_name="shot"
    template = '{0}/index.html'.format(node_name)

    return render_template(template,
        title=node_name,
        nodes=nodes,
        type_names=type_names())

@nodes.route("/view/<node_id>")
def view(node_id):
    node = Node.find(node_id)
    if node:
        return render_template('{0}/view.html'.format('shot'),
            node=node,
            type_names=type_names())
    else:
        abort(404)

@nodes.route("/<node_type>/add", methods=['GET', 'POST'])
def add(node_type):
    """Generic function to add a node of any type
    """
    ntype = NodeType.find(node_type)
    form = get_node_form(ntype)
    if form.validate_on_submit():
        if process_node_form(form):
            flash('Node correctly added.')
            return redirect('/')
    else:
        print form.errors
    return render_template('nodes/add.html',
        node_type=ntype,
        form=form,
        errors=form.errors,
        type_names=type_names())


@nodes.route("/<node_id>/edit", methods=['GET', 'POST'])
def edit(node_id):
    """Generic node editing form
    """
    node = Node.find(node_id)
    node_type = NodeType.find(node.node_type)
    form = get_node_form( node_type )

    if form.validate_on_submit():
        if process_node_form(form, node_id):
            node = Node.find(node_id)
            form = get_node_form( node_type )
            flash ("Node correctly edited.")
            return redirect('/')
        else:
            print ("ERROR")
    else:
        form.name.data = node.name
        form.description.data = node.description
        form.thumbnail.data = node.thumbnail

        prop_dict = node.properties.to_dict()
        for prop in prop_dict:
            for field in form:
                if field.name == prop:
                    value = prop_dict[prop]
                    field.data = value
                    break

    return render_template('nodes/edit.html',
        node=node,
        form=form,
        type_names=type_names())


@nodes.route("/<node_id>/delete", methods=['GET', 'POST'])
def delete(node_id):
    """Generic node deletion
    """
    node = Node.find(node_id)
    if node.delete():
        flash('Node correctly deleted.')
        return redirect('/')
    else:
        return redirect(url_for('node.edit', node_id=node._id))
