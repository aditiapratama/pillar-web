from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for

from attractsdk import NodeType
from application.modules.nodes.forms import NodeTypeForm


# Name of the Blueprint
node_types = Blueprint('node_types', __name__)


@node_types.route("/")
def index():
    """Display the node types
    """
    node_types = NodeType.all()
    node_types = node_types['_items']
    return render_template('node_types/index.html',
                           title='node_types',
                           node_types=node_types)


@node_types.route("/add", methods=['GET', 'POST'])
def add():
    form = NodeTypeForm()
    if form.validate_on_submit():
        NodeType(
            name=form.name.data,
            description=form.description.data,
            url=form.url.data)

        return redirect(url_for('node_types.index'))
    return render_template('node_types/add.html', form=form)


@node_types.route("/<node_type_id>/edit", methods=['GET', 'POST'])
def edit(node_type_id):
    node_type = NodeType.find(node_type_id)
    form = NodeTypeForm(obj=node_type)
    if form.validate_on_submit():
        node_type.name = form.name.data
        node_type.description = form.description.data
        node_type.url = form.url.data
        # Processing custom fields
        for field in form.properties:
            print field.data['id']
    else:
        print form.errors
    return render_template('node_types/edit.html',
                           node_type=node_type,
                           form=form)
