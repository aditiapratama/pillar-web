from flask_wtf import Form
from wtforms import FieldList
from wtforms import FormField
from wtforms import TextField
from wtforms import FileField
from wtforms import SelectField
from wtforms import HiddenField
from wtforms import BooleanField
from wtforms import TextAreaField
import attractsdk
from wtforms import DateTimeField
from wtforms import Form as BasicForm
from wtforms.validators import DataRequired

from datetime import datetime

from application import SystemUtility


RFC1123_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'


class CustomFieldForm(BasicForm):
    id = HiddenField()
    field_type = TextField('Field Type', validators=[DataRequired()])
    name = TextField('Name', validators=[DataRequired()])
    name_url = TextField('Url', validators=[DataRequired()])
    description = TextAreaField('Description')
    parent = TextField('Parent')
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

    api = SystemUtility.attract_api()
    node_schema = node_type['dyn_schema'].to_dict()
    form_prop = node_type['form_schema'].to_dict()
    parent_prop = node_type['parent'].to_dict()

    setattr(ProceduralForm,
        'name',
        TextField('Name', validators=[DataRequired()]))
    # Parenting
    if len(parent_prop['node_types']) > 0:
        # TODO support more than 1 type
        parent_type = parent_prop['node_types'][0]
        select = []
        ntype = attractsdk.NodeType.all(
            {'where': 'name=="{0}"'.format(parent_type)}, api=api)
        nodes = attractsdk.Node.all(
            {'where': 'node_type=="{0}"'.format(
                ntype['_items'][0]['_id'])}, api=api)
        for option in nodes['_items']:
            select.append((str(option['_id']), str(option['name'])))
        setattr(ProceduralForm,
                'parent',
                SelectField('Parent {0}'.format(parent_type), choices=select))

    setattr(ProceduralForm,
        'description',
        TextAreaField('Description'))
    setattr(ProceduralForm,
        'picture',
        FileField('Picture'))
    setattr(ProceduralForm,
        'node_type_id',
        HiddenField(default=node_type._id))

    def build_form(node_schema, form_schema, prefix=""):
        for prop in node_schema:
            schema_prop = node_schema[prop]
            form_prop = form_schema[prop]
            if prop == 'items':
                continue
            if 'visible' in form_prop and not form_prop['visible']:
                continue
            prop_name = "{0}{1}".format(prefix, prop)
            if schema_prop['type']=='dict':
                build_form(schema_prop['schema'], form_prop['schema'], "{0}->".format(prop_name))
                continue
            if 'allowed' in schema_prop:
                select = []
                for option in schema_prop['allowed']:
                    select.append((str(option), str(option)))
                setattr(ProceduralForm,
                        prop_name,
                        SelectField(choices=select))
            elif schema_prop['type']=='datetime':
                setattr(ProceduralForm,
                        prop_name,
                        DateTimeField(prop_name, default=datetime.now()))
            elif 'maxlength' in schema_prop and schema_prop['maxlength']>64:
                setattr(ProceduralForm,
                        prop_name,
                        TextAreaField(prop_name))
            else:
                setattr(ProceduralForm,
                        prop_name,
                        TextField(prop_name))

    build_form(node_schema, form_prop)

    return ProceduralForm()


def process_node_form(form, node_id=None, node_type=None, user=None):
    """Generic function used to process new nodes, as well as edits
    """
    api = SystemUtility.attract_api()
    node_schema = node_type['dyn_schema'].to_dict()
    form_schema = node_type['form_schema'].to_dict()

    if node_id:
        # Update existing node
        print ("UPDATE")
        node = attractsdk.Node.find(node_id, api=api)
        node.name = form.name.data
        node.description = form.description.data
        if 'parent' in form:
            node.parent = form.parent.data
        def update_data(node_schema, form_schema, prefix=""):
            print (node_schema)
            for pr in node_schema:
                schema_prop = node_schema[pr]
                form_prop = form_schema[pr]
                if pr == 'items':
                    continue
                if 'visible' in form_prop and not form_prop['visible']:
                    continue
                prop_name = "{0}{1}".format(prefix, pr)
                if schema_prop['type']=='dict':
                    update_data(
                        schema_prop['schema'],
                        form_prop['schema'],
                        "{0}->".format(prop_name))
                    continue
                data = form[prop_name].data
                if schema_prop['type'] == 'integer':
                    if data == '':
                        data = 0
                    else:
                        data = int(form[prop_name].data)
                if schema_prop['type'] == 'datetime':
                    data = datetime.strftime(data, RFC1123_DATE_FORMAT)
                else:
                    if pr in form:
                        data = form[prop_name].data
                path = prop_name.split('->')
                if len(path)>1:
                    pass
                else:
                    node.properties[prop_name] = data
        update_data(node_schema, form_schema)
        update = node.update(api=api)
        print ("UPDATE")
        print (update)
        return update
    else:
        # Create a new node
        node = attractsdk.Node()
        prop = {}
        prop['name'] = form.name.data
        prop['description'] = form.description.data
        prop['user'] = user
        if 'parent' in form:
            prop['parent'] = form.parent.data
        prop['properties'] = {}

        def get_data(node_schema, form_schema, prefix=""):
            for pr in node_schema:
                schema_prop = node_schema[pr]
                form_prop = form_schema[pr]
                if pr == 'items':
                    continue
                if 'visible' in form_prop and not form_prop['visible']:
                    continue
                prop_name = "{0}{1}".format(prefix, pr)
                if schema_prop['type'] == 'dict':
                    get_data(
                        schema_prop['schema'],
                        form_prop['schema'],
                        "{0}->".format(prop_name))
                    continue
                data = form[prop_name].data
                if schema_prop['type'] == 'integer':
                    if data == '':
                        data = 0
                if schema_prop['type'] == 'list':
                    if data == '':
                        data = []
                if schema_prop['type'] == 'datetime':
                    data = datetime.strftime(data, RFC1123_DATE_FORMAT)
                path = prop_name.split('->')
                if len(path) > 1:
                    def recursive(path, rdict, data):
                        item = path.pop(0)
                        if not item in rdict:
                            rdict[item] = {}
                        if len(path)>0:
                            rdict[item] = recursive (path, rdict[item], data)
                        else:
                            rdict[item] = data
                        return rdict
                    prop['properties'] = recursive(path, prop['properties'], data)
                else:
                    prop['properties'][prop_name] = data

        get_data(node_schema, form_schema)
        print (prop)

        prop['node_type'] = form.node_type_id.data
        # Pardon the local path, this is for testing purposes and will be removed
        # files = {'picture': open('/Users/fsiddi/Desktop/1500x500.jpeg', 'rb')}
        files = None
        post = node.post(prop, files=files, api=api)
        return post
