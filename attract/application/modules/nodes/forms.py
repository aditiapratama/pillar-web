import attractsdk
from attractsdk import Node

from flask_wtf import Form
from wtforms import FieldList
from wtforms import FormField
from wtforms import TextField
from wtforms import FileField
from wtforms import DateField
from wtforms import SelectField
from wtforms import HiddenField
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import TextAreaField
from wtforms import DateTimeField
from wtforms import SelectMultipleField
from wtforms import Form as BasicForm
from wtforms.validators import DataRequired
from wtforms.widgets import HiddenInput
from wtforms.widgets import HTMLString
from wtforms.widgets import Select

from datetime import datetime
from datetime import date

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
        super(ModelFieldList, self).populate_obj(obj, name)


class ChildInline(Form):
    title = TextField('Title',)


class NodeTypeForm(Form):
    name = TextField('Name', validators=[DataRequired()])
    url = TextField('Url', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    is_extended = BooleanField('Is extended')
    properties = ModelFieldList(FormField(CustomFieldForm), model=CustomFields)


def hiddenValue(data):
    """Function for field._value
    on custom hidden Fields"""
    def hidden_value ():
        return data
    return hidden_value


def set_hidden(field, data):
    """change field to hidden"""
    hiddenInput = HiddenInput()
    field.widget = hiddenInput
    field.data = data
    field._value = hiddenValue(data)


class FileSelect(Select):
    def __init__(self, **kwargs):
        self.is_multiple = kwargs.get('multiple')
        super(FileSelect, self).__init__(**kwargs)

    def __call__(self, field, **kwargs):
        html =  super(FileSelect, self).__call__(field, **kwargs)
        if self.is_multiple:
            multiple_value = 'true';
        else:
            multiple_value = 'false';
        button= """
<button onclick="set_upload_parameters('{0}', {1});" style="margin-top: 5px;" type="button" class="btn btn-primary" data-toggle="modal" data-target="#fileUploaderModal">
  Upload Files
</button>""".format(field.id, multiple_value)
        return HTMLString(html+button)


class FileSelectField(SelectField):
    def __init__(self, name, **kwargs):
        super(FileSelectField, self).__init__(name, **kwargs)
        self.widget = FileSelect()


class FileSelectMultipleField(SelectMultipleField):
    def __init__(self, **kwargs):
        super(FileSelectMultipleField, self).__init__(**kwargs)
        self.widget = FileSelect(multiple=True)


def get_comment_form(node, comment_type):
    form = get_node_form(comment_type)
    for field in form:
        if field.name == 'parent':
            field = set_hidden(field, str(node._id))
        elif field.name in ['name',
                            'description',
                            'picture',
                            'picture_file']:
            data = field.data
            if field.name == 'name':
                data = "Comment on {0}".format(node.name)
            elif field.name == 'description':
                data = "Comment on {0}, by {1}".format(node.name, node.user)
            elif field.name == 'attachments':
                data = ""
            field = set_hidden(field, data)
    return form


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
    if 'node_types' in parent_prop and len(parent_prop['node_types']) > 0:
        select = []
        for parent_type in parent_prop['node_types']:
            parent_node_type = attractsdk.NodeType.all(
                {'where': 'name=="{0}"'.format(parent_type)}, api=api)
            nodes = Node.all({
                'where': 'node_type=="{0}"'.format(
                    str(parent_node_type._items[0]['_id'])),
                'max_results': 999,
                'sort': "order"},
                api=api)
            for option in nodes._items:
                select.append((str(option._id), str(option.name)))

        parent_names = ""
        for parent_type in parent_prop['node_types']:
            parent_names = "{0} {1},".format(parent_names, parent_type)

        setattr(ProceduralForm,
                'parent',
                SelectField('Parent ({0})'.format(parent_names),
                            choices=select))

    setattr(ProceduralForm,
        'description',
        TextAreaField('Description'))
    #setattr(ProceduralForm,
    #    'picture',
    #    FileField('Picture'))
    select = []
    select.append(('None', 'None'))
    nodes = attractsdk.File.all(
        {'max_results': 999, 'where': '{"is_preview" : {"$ne":true}}'},
        api=api)
    for option in nodes['_items']:
        try:
            select.append((str(option['_id']), str(option['name'])))
        except KeyError:
            select.append((str(option['_id']), str(option['filename'])))
    # setattr(ProceduralForm,
    #         'picture_file',
    #         FileField('Picture File'))
    setattr(ProceduralForm,
        'picture',
        FileSelectField('Picture', choices=select))
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
            if schema_prop['type'] == 'dict':
                build_form(schema_prop['schema'],
                           form_prop['schema'],
                           "{0}__".format(prop_name))
                continue
            if schema_prop['type'] == 'list' and 'items' in form_prop:
                for item in form_prop['items']:
                    items = eval("attractsdk.{0}".format(item[0]))
                    items_to_select = items.all({'max_results': 200}, api=api)
                    if items_to_select:
                        items_to_select = items_to_select["_items"]
                    else:
                        items_to_select = []
                    select = []
                    for select_item in items_to_select:
                        try:
                            select.append((select_item['_id'], select_item[item[1]]))
                        except KeyError:
                            # Backwards compatibility
                            select.append((select_item['_id'], select_item['_id']))
                    if item[0] == 'File':
                        setattr(ProceduralForm,
                                prop_name,
                                FileSelectMultipleField(choices=select))
                    else:
                        setattr(ProceduralForm,
                                prop_name,
                                SelectMultipleField(choices=select))
            elif 'allowed' in schema_prop:
                select = []
                for option in schema_prop['allowed']:
                    select.append((str(option), str(option)))
                setattr(ProceduralForm,
                        prop_name,
                        SelectField(choices=select))
            elif schema_prop['type'] == 'datetime':
                if 'dateonly' in form_prop and form_prop['dateonly']:
                    setattr(ProceduralForm,
                            prop_name,
                            DateField(prop_name, default=date.today()))
                else:
                    setattr(ProceduralForm,
                            prop_name,
                            DateTimeField(prop_name, default=datetime.now()))
            elif schema_prop['type'] == 'integer':
                setattr(ProceduralForm,
                        prop_name,
                        IntegerField(prop_name))
            elif schema_prop['type'] == 'media':
                setattr(ProceduralForm,
                        prop_name,
                        FileField(prop_name))
            elif 'maxlength' in schema_prop and schema_prop['maxlength'] > 64:
                setattr(ProceduralForm,
                        prop_name,
                        TextAreaField(prop_name))
            else:
                setattr(ProceduralForm,
                        prop_name,
                        TextField(prop_name))

    build_form(node_schema, form_prop)

    return ProceduralForm()


def recursive(path, rdict, data):
    item = path.pop(0)
    if not item in rdict:
        rdict[item] = {}
    if len(path)>0:
        rdict[item] = recursive (path, rdict[item], data)
    else:
        rdict[item] = data
    return rdict


def process_node_form(form, node_id=None, node_type=None, user=None):
    """Generic function used to process new nodes, as well as edits
    """
    if not user:
        print ("User is None")
        return False
    api = SystemUtility.attract_api()
    node_schema = node_type['dyn_schema'].to_dict()
    form_schema = node_type['form_schema'].to_dict()

    if node_id:
        # Update existing node
        node = attractsdk.Node.find(node_id, api=api)
        node.name = form.name.data
        node.description = form.description.data
        if 'picture' in form:
            node.picture = form.picture.data
            if node.picture == "None":
                node.picture = None
        if 'parent' in form:
            node.parent = form.parent.data
        def update_data(node_schema, form_schema, prefix=""):
            for pr in node_schema:
                schema_prop = node_schema[pr]
                form_prop = form_schema[pr]
                if pr == 'items':
                    continue
                if 'visible' in form_prop and not form_prop['visible']:
                    continue
                prop_name = "{0}{1}".format(prefix, pr)
                if schema_prop['type'] == 'dict':
                    update_data(
                        schema_prop['schema'],
                        form_prop['schema'],
                        "{0}__".format(prop_name))
                    continue
                data = form[prop_name].data
                if schema_prop['type'] == 'dict':
                    if data == 'None':
                        continue
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
                path = prop_name.split('__')
                if len(path) > 1:
                    recursive_prop = recursive(
                        path, node.properties.to_dict(), data)
                    node.properties = recursive_prop
                else:
                    node.properties[prop_name] = data
        update_data(node_schema, form_schema)
        # send_file(form, node, user)
        update = node.update(api=api)
        # if form.picture.data:
        #     image_data = request.files[form.picture.name].read()
        #     post = node.replace_picture(image_data, api=api)
        return update
    else:
        # Create a new node
        node = attractsdk.Node()
        prop = {}
        files = {}
        prop['name'] = form.name.data
        prop['description'] = form.description.data
        prop['user'] = user
        if 'picture' in form:
            prop['picture'] = form.picture.data
            if prop['picture'] == 'None':
                prop['picture'] = None
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
                        "{0}__".format(prop_name))
                    continue
                data = form[prop_name].data
                if schema_prop['type'] == 'media':
                    tmpfile = '/tmp/binary_data'
                    data.save(tmpfile)
                    binfile = open(tmpfile, 'rb')
                    files[pr] = binfile
                    continue
                if schema_prop['type'] == 'integer':
                    if data == '':
                        data = 0
                if schema_prop['type'] == 'list':
                    if data == '':
                        data = []
                if schema_prop['type'] == 'datetime':
                    data = datetime.strftime(data, RFC1123_DATE_FORMAT)
                path = prop_name.split('__')
                if len(path) > 1:
                    prop['properties'] = recursive(path, prop['properties'], data)
                else:
                    prop['properties'][prop_name] = data

        get_data(node_schema, form_schema)

        prop['node_type'] = form.node_type_id.data
        # Pardon the local path, this is for testing purposes and will be removed
        # files = {'picture': open('/Users/fsiddi/Desktop/1500x500.jpeg', 'rb')}
        # send_file(form, prop, user)
        post = node.post(prop, api=api)

        return post
