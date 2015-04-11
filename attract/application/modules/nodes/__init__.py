import attractsdk

from flask import abort
from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import flash
from flask import url_for
from flask import session

from application.modules.nodes.forms import get_node_form
from application.modules.nodes.forms import process_node_form

from application import SystemUtility

# Name of the Blueprint
nodes = Blueprint('nodes', __name__)

def type_names():
    api = SystemUtility.attract_api()

    types = attractsdk.NodeType.all(api=api)["_items"]
    type_names = []
    for names in types:
        type_names.append(str(names['name']))
    return type_names


@nodes.route("/<node_name>", methods=['GET', 'POST'])
def index(node_name=""):
    """Generic function to list all nodes
    """
    api = SystemUtility.attract_api()
    if node_name == "":
        node_name = "shot"

    node_type_list = attractsdk.NodeType.all({'where': "name=='{0}'".format(node_name)}, api=api)
    node_type = node_type_list['_items'][0]
    nodes = attractsdk.Node.all({
        'where': "node_type=='{0}'".format(node_type['_id']),
        'sort' : "order"}, api=api)
    nodes = nodes['_items']
    template = '{0}/index.html'.format(node_name)

    return render_template(template,
        title=node_name,
        nodes=nodes,
        node_type=node_type,
        type_names=type_names(),
        email=SystemUtility.session_email())

@nodes.route("/view/<node_id>")
def view(node_id):
    api = SystemUtility.attract_api()
    node = attractsdk.Node.find(node_id, api=api)
    if node:
        return render_template('{0}/view.html'.format('shot'),
            node=node,
            type_names=type_names(),
            email=SystemUtility.session_email())
    else:
        abort(404)

@nodes.route("/<node_type>/add", methods=['GET', 'POST'])
def add(node_type):
    """Generic function to add a node of any type
    """
    api = SystemUtility.attract_api()
    ntype = attractsdk.NodeType.find(node_type, api=api)
    form = get_node_form(ntype)
    email = SystemUtility.session_email()
    if form.validate_on_submit():
        if process_node_form(form, node_type=ntype, user=email):
            flash('Node correctly added.')
            return redirect(url_for('nodes.index', node_name=ntype['name']))
    else:
        print form.errors
    return render_template('nodes/add.html',
        node_type=ntype,
        form=form,
        errors=form.errors,
        type_names=type_names(),
        email=email)


@nodes.route("/<node_id>/edit", methods=['GET', 'POST'])
def edit(node_id):
    """Generic node editing form
    """
    api = SystemUtility.attract_api()
    node = attractsdk.Node.find(node_id, api=api)
    node_type = attractsdk.NodeType.find(node.node_type, api=api)
    form = get_node_form(node_type)

    if form.validate_on_submit():
        if process_node_form(form, node_id=node_id, node_type=node_type):
            node = attractsdk.Node.find(node_id, api=api)
            form = get_node_form( node_type )
            flash ("Node correctly edited.")
            return redirect(url_for('nodes.index', node_name=node_type['name']))
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
        type_names=type_names(),
        email=SystemUtility.session_email())


@nodes.route("/<node_id>/delete", methods=['GET', 'POST'])
def delete(node_id):
    """Generic node deletion
    """
    api = SystemUtility.attract_api()
    node = attractsdk.Node.find(node_id, api=api)
    if node.delete(api=api):
        flash('Node correctly deleted.')
        return redirect('/')
    else:
        return redirect(url_for('node.edit', node_id=node._id))
