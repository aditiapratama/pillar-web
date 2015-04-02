from flask_wtf import Form
# from wtforms import Form as BasicForm
from wtforms import TextField
from wtforms import BooleanField
from wtforms.validators import DataRequired


class UserLoginForm(Form):
    # id = HiddenField()
    email = TextField('EMail', validators=[DataRequired()])
    password = TextField('Password', validators=[DataRequired()])
    # name_url = TextField('Url', validators=[DataRequired()])
    # description = TextAreaField('Description')
    remember_me = BooleanField('Remember Me')

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(UserLoginForm, self).__init__(csrf_enabled=False, *args, **kwargs)

'''from wtforms import SelectField
from wtforms import TextAreaField
from wtforms import IntegerField
from wtforms import HiddenField
from wtforms import FieldList
from wtforms import FormField
from wtforms import Form as BasicForm

from attractsdk import Node
from attractsdk import NodeType

#from application.modules.nodes.models import CustomFields

#from application import db

#from application.modules.nodes.models import Node, NodeType, NodeProperties

class CustomFieldForm(BasicForm):
    id = HiddenField()
    field_type = TextField('Field Type', validators=[DataRequired()])
    name = TextField('Name', validators=[DataRequired()])
    name_url = TextField('Url', validators=[DataRequired()])
    description = TextAreaField('Description')
    is_required = BooleanField('Is extended')
    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(CustomFieldForm, self).__init__(csrf_enabled=False, *args, **kwargs)


class CustomFields():
    id = 1
    node_id = 2
    custom_field_id = 3
    custom_field = 4
    calue = "Value"


class ModelFieldList(FieldList):
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop("model", None)
        super(ModelFieldList, self).__init__(*args, **kwargs)
        if not self.model:
            raise ValueError("ModelFieldList requires model to be set")

    def populate_obj(self, obj, name):
        """while len(getattr(obj, name)) < len(self.entries):
            newModel = self.model()
            # db.session.add(newModel)
            getattr(obj, name).append(newModel)
        while len(getattr(obj, name)) > len(self.entries):
            # db.session.delete(getattr(obj, name).pop())
            pass"""
        testModel = CustomFields()
        getattr(obj, name).append(testModel)
        # print ("testModel")
        # print (obj.get(name))
        super(ModelFieldList, self).populate_obj(obj, name)

class ChildInline(Form):
    title = TextField('Title',)

class NodeTypeForm(Form):
    name = TextField('Name', validators=[DataRequired()])
    url = TextField('Url', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    is_extended = BooleanField('Is extended')
    properties = ModelFieldList(FormField(CustomFieldForm), model=CustomFields)


"""
class IMForm(Form):
    protocol = SelectField(choices=[('aim', 'AIM'), ('msn', 'MSN')])
    username = TextField()

class ContactForm(Form):
    first_name  = TextField()
    last_name   = TextField()
    im_accounts = FieldList(BooleanField('Is extended'),)
"""


def get_node_form(node_type):
    class ProceduralForm(Form):
        pass

    node_schema = node_type['dyn_schema'].to_dict()

    setattr(ProceduralForm,
        'name',
        TextField('Name', validators=[DataRequired()]))
    setattr(ProceduralForm,
        'description',
        TextAreaField('Description'))
    setattr(ProceduralForm,
        'thumbnail',
        TextField('Thumbnail'))
    setattr(ProceduralForm,
        'node_type_id',
        HiddenField(default=node_type._id))

    for prop in node_schema:
        schema_prop = node_schema[prop]
        if 'allowed' in schema_prop:
            select = []
            for option in schema_prop['allowed']:
                select.append((str(option), str(option)))
            setattr(ProceduralForm,
                    prop,
                    SelectField(choices=select))
        elif 'maxlength' in schema_prop and schema_prop['maxlength']>64:
            setattr(ProceduralForm,
                    prop,
                    TextAreaField(prop))
        else:
            setattr(ProceduralForm,
                    prop,
                    TextField(prop))

    return ProceduralForm()


def process_node_form(form, node_id=None):
    """Generic function used to process new nodes, as well as edits
    """
    if node_id:
        node = Node.find(node_id)
        node.name = form.name.data
        node.description = form.description.data
        node.thumbnail = form.thumbnail.data
        node.properties.status = form.status.data
        node.properties.url = form.url.data
        node.properties.notes = form.notes.data
        if form.cut_in.data == '':
            form.cut_in.data = 0
        node.properties.cut_in = int(form.cut_in.data)
        node.properties.shot_group = form.shot_group.data
        if form.cut_out.data == '':
            form.cut_out.data = 0
        node.properties.cut_out = int(form.cut_out.data)
        if form.order.data == '':
            form.order.data = 0
        node.properties.order = int(form.order.data)
        update = node.update()
        return update
    else:
        node = Node()
        prop = {}
        prop['name'] = form.name.data
        prop['description'] = form.description.data
        prop['thumbnail'] = form.thumbnail.data
        prop['properties'] = {}
        prop['properties']['status'] = form.status.data
        prop['properties']['url'] = form.url.data
        prop['properties']['notes'] = form.notes.data
        if form.cut_in.data == '':
            form.cut_in.data = 0
        prop['properties']['cut_in'] = int(form.cut_in.data)
        prop['properties']['shot_group'] = form.shot_group.data
        if form.cut_out.data == '':
            form.cut_out.data = 0
        prop['properties']['cut_out'] = int(form.cut_out.data)
        if form.order.data == '':
            form.order.data = 0
        prop['properties']['order'] = int(form.order.data)
        #
        prop['node_type'] = form.node_type_id.data
        post = node.post(prop)
        return post'''
