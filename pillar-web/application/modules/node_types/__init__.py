from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask.ext.login import login_required
from pillarsdk import NodeType
from application import system_util

# Name of the Blueprint
node_types = Blueprint('node_types', __name__)


@node_types.route("/")
@login_required
def index():
    """Display the node types
    """
    api = system_util.pillar_api()
    node_types = NodeType.all(api=api)
    node_types = node_types['_items']
    return render_template('node_types/index.html',
                           title='node_types',
                           node_types=node_types)


@node_types.route("/add", methods=['GET', 'POST'])
@login_required
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
@login_required
def edit(node_type_id):
    node_type = NodeType.find(node_type_id)
    form = NodeTypeForm(obj=node_type)
    if form.validate_on_submit():
        node_type.name = form.name.data
        node_type.description = form.description.data
        node_type.url = form.url.data
        # Processing custom fields
        for field in form.properties:
            pass
            #print field.data['id']
    else:
        if form.errors:
            print form.errors
    return render_template('node_types/edit.html',
                           node_type=node_type,
                           form=form)
