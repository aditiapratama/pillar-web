from flask_wtf import Form
from wtforms import TextField
from wtforms import BooleanField
from wtforms import SelectField
from wtforms import TextAreaField
# from wtforms import IntegerField
from wtforms import HiddenField
from wtforms import FieldList
from wtforms import FormField
from wtforms import Form as BasicForm

#from attractsdk import Node
#from attractsdk import NodeType
import attractsdk
from application import SystemUtility

#from application.modules.nodes.models import CustomFields
from wtforms.validators import DataRequired

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

    def build_form(node_schema, prefix=""):
        for prop in node_schema:
            schema_prop = node_schema[prop]
            prop_name = "{0}{1}".format(prefix, prop)
            if schema_prop['type']=='dict':
                build_form(schema_prop['schema'], "{0}->".format(prop_name))
                continue
            if 'allowed' in schema_prop:
                select = []
                for option in schema_prop['allowed']:
                    select.append((str(option), str(option)))
                setattr(ProceduralForm,
                        prop_name,
                        SelectField(choices=select))
            elif 'maxlength' in schema_prop and schema_prop['maxlength']>64:
                setattr(ProceduralForm,
                        prop_name,
                        TextAreaField(prop_name))
            else:
                setattr(ProceduralForm,
                        prop_name,
                        TextField(prop_name))

    build_form(node_schema)

    return ProceduralForm()


def process_node_form(form, node_id=None, node_type=None, user=None):
    """Generic function used to process new nodes, as well as edits
    """
    api = SystemUtility.attract_api()
    node_schema = node_type['dyn_schema'].to_dict()
    if node_id:
        node = attractsdk.Node.find(node_id, api=api)
        node.name = form.name.data
        node.description = form.description.data
        node.thumbnail = form.thumbnail.data
        def get_data(node_schema, prefix=""):
            for pr in node_schema:
                schema_prop = node_schema[pr]
                prop_name = "{0}{1}".format(prefix, pr)
                if schema_prop['type']=='dict':
                    get_data(schema_prop['schema'], "{0}->".format(prop_name))
                    continue
                data = form[prop_name].data
                if schema_prop['type'] == 'integer':
                    if data == '':
                        data = 0
                    else:
                        data = int(form[prop_name].data)
                else:
                    if pr in form:
                        data = form[prop_name].data
                path = prop_name.split('->')
                if len(path)>1:
                    pass
                else:
                    node.properties[prop_name] = data
        get_data(node_schema)
        update = node.update(api=api)
        return update
    else:
        node = attractsdk.Node()
        prop = {}
        prop['name'] = form.name.data
        prop['description'] = form.description.data
        prop['thumbnail'] = form.thumbnail.data
        prop['user'] = user
        prop['properties'] = {}

        def get_data(node_schema, prefix=""):
            for pr in node_schema:
                schema_prop = node_schema[pr]
                prop_name = "{0}{1}".format(prefix, pr)
                if schema_prop['type']=='dict':
                    get_data(schema_prop['schema'], "{0}->".format(prop_name))
                    continue
                data = form[prop_name].data
                if schema_prop['type'] == 'integer':
                    if data == '':
                        data = 0
                path = prop_name.split('->')
                if len(path)>1:
                    pass
                else:
                    prop['properties'][prop_name] = data

        get_data(node_schema)

        prop['node_type'] = form.node_type_id.data
        post = node.post(prop, api=api)
        return post
