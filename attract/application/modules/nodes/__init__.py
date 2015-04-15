from attractsdk import Node
from attractsdk import NodeType
from attractsdk.exceptions import UnauthorizedAccess

from flask import abort
from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import flash
from flask import url_for
from flask import session
from flask import request

from datetime import datetime

from application.modules.nodes.forms import get_node_form
from application.modules.nodes.forms import process_node_form
from application.helpers import Pagination

from application import SystemUtility


RFC1123_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'


# Name of the Blueprint
nodes = Blueprint('nodes', __name__)

def type_names():
    api = SystemUtility.attract_api()

    types = NodeType.all(api=api)["_items"]
    type_names = []
    for names in types:
        type_names.append(str(names['name']))
    return type_names


@nodes.route("/<node_name>")
def index(node_name=""):
    """Generic function to list all nodes
    """
    # Pagination index
    page = request.args.get('page', 1)
    max_results = 100

    api = SystemUtility.attract_api()
    if node_name == "":
        node_name = "shot"

    node_type_list = NodeType.all({'where': "name=='{0}'".format(node_name)}, api=api)

    node_type = node_type_list['_items'][0]
    nodes = Node.all({
        'where': '{"node_type" : "%s"}' % (node_type['_id']),
        'max_results': max_results,
        'page': page,
        #'where': "status!='deleted'",
        'sort' : "order"}, api=api)

    # Build the pagination object
    pagination = Pagination(int(page), max_results, nodes._meta.total)

    template = '{0}/index.html'.format(node_name)

    return render_template(template,
        title=node_name,
        nodes=nodes,
        node_type=node_type,
        type_names=type_names(),
        pagination=pagination,
        email=SystemUtility.session_item('email'))


@nodes.route("/<node_id>/view")
def view(node_id):
    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)
    node_type = NodeType.find(node['node_type'], api=api)
    if node:
        try:
            parent = Node.find(node['parent'], api=api)
        except KeyError:
            parent = None
        children = Node.all(
            {'where': 'parent==ObjectId("%s")' % node['_id']}, api=api)

        children = children.to_dict()['_items']
        return render_template(
            '{0}/view.html'.format(node_type['name']),
            node=node,
            type_names=type_names(),
            parent=parent,
            children=children,
            email=SystemUtility.session_item('email'))
    else:
        return abort(404)


@nodes.route("/<node_type_id>/add", methods=['GET', 'POST'])
def add(node_type_id):
    """Generic function to add a node of any type
    """
    api = SystemUtility.attract_api()
    ntype = NodeType.find(node_type_id, api=api)
    form = get_node_form(ntype)
    user_id = SystemUtility.session_item('user_id')
    email = SystemUtility.session_item('email')
    if form.validate_on_submit():
        if process_node_form(form, node_type=ntype, user=user_id):
            flash('Node correctly added')
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
    node = Node.find(node_id, api=api)
    node_type = NodeType.find(node.node_type, api=api)
    form = get_node_form(node_type)
    user_id = SystemUtility.session_item('user_id')
    node_schema = node_type['dyn_schema'].to_dict()
    form_schema = node_type['form_schema'].to_dict()
    error = ""

    if form.validate_on_submit():
        if process_node_form(
                form, node_id=node_id, node_type=node_type, user=user_id):
            node = Node.find(node_id, api=api)
            form = get_node_form( node_type )
            flash ('Node "{0}" correctly edited'.format(node.name))
            return redirect(url_for('nodes.index', node_name=node_type['name']))
        else:
            error = "Server error"
            print ("Error sending data")
    else:
        # Populate Form
        form.name.data = node.name
        form.description.data = node.description
        form.picture.data = node.picture
        if node.parent:
            form.parent.data = node.parent

        def set_properties(
                node_schema, form_schema, prop_dict, form, prefix=""):
            for prop in node_schema:
                if not prop in prop_dict:
                    continue
                schema_prop = node_schema[prop]
                form_prop = form_schema[prop]
                prop_name = "{0}{1}".format(prefix, prop)
                if schema_prop['type'] == 'dict':
                    set_properties(
                        schema_prop['schema'],
                        form_prop['schema'],
                        prop_dict[prop_name],
                        form,
                        "{0}->".format(prop_name))
                else:
                    try:
                        data = prop_dict[prop]
                    except KeyError:
                        print ("{0} not found in form".format(prop_name))
                    if schema_prop['type'] == 'datetime':
                        data = datetime.strptime(data, RFC1123_DATE_FORMAT)
                    if prop_name in form:
                        form[prop_name].data = data


        prop_dict = node.properties.to_dict()
        set_properties(node_schema, form_schema, prop_dict, form)

    return render_template('nodes/edit.html',
        node=node,
        form=form,
        errors=form.errors,
        error=error,
        type_names=type_names(),
        email=SystemUtility.session_item('email'))


@nodes.route("/<node_id>/delete", methods=['GET', 'POST'])
def delete(node_id):
    """Generic node deletion
    """
    api = SystemUtility.attract_api()
    node = Node.find(node_id, api=api)
    name = node.name
    if node.delete(api=api):
        flash('Node "{0}" correctly deleted'.format(name))
        return redirect('/')
    else:
        return redirect(url_for('node.edit', node_id=node._id))
