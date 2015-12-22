import json
import pillarsdk
from pillarsdk import Node
from flask import url_for
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
from wtforms import FloatField
from wtforms import TextAreaField
from wtforms import DateTimeField
from wtforms import SelectMultipleField
from wtforms import Form as BasicForm
from wtforms.validators import DataRequired
from wtforms.widgets import HiddenInput
from wtforms.widgets import HTMLString
from wtforms.widgets import Select
from wtforms.widgets import TextInput
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


class FileSelectText(HiddenInput):
    def __init__(self, **kwargs):
        super(FileSelectText, self).__init__(**kwargs)

    def __call__(self, field, **kwargs):
        html =  super(FileSelectText, self).__call__(field, **kwargs)
        button = """
        <input class="fileupload" type="file" name="file" data-url="{0}" data-field-name="{1}">
        <div class="picture-progress">
          <div class="picture-progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;">
          </div>
        </div>""".format(url_for('files.upload'), field.name)
        return HTMLString(html + button)


class FileSelectField(TextField):
    def __init__(self, name, **kwargs):
        super(FileSelectField, self).__init__(name, **kwargs)
        self.widget = FileSelectText()


class FileSelectAttachment(HiddenInput):
    def __init__(self, **kwargs):
        super(FileSelectAttachment, self).__init__(**kwargs)

    def __call__(self, field, **kwargs):
        html =  super(FileSelectAttachment, self).__call__(field, **kwargs)
        button = """
        <input class="fileupload" type="file" name="file" data-url="{0}" data-field-name="{1}">
        <div class="picture-progress">
          <div class="picture-progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;">
          </div>
        </div>""".format(url_for('files.upload'), field.name)
        return HTMLString(html + button)


class AttachmentSelectField(TextField):
    def __init__(self, name, **kwargs):
        super(AttachmentSelectField, self).__init__(name, **kwargs)
        self.widget = FileSelectAttachment()


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

        parent_names = ""
        for parent_type in parent_prop['node_types']:
            parent_names = "{0} {1},".format(parent_names, parent_type)

        setattr(ProceduralForm,
                'parent',
                HiddenField('Parent ({0})'.format(parent_names)))

    setattr(ProceduralForm,
        'description',
        TextAreaField('Description'))
    setattr(ProceduralForm,
        'picture',
        FileSelectField('Picture'))
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

            # Recursive call if detects a dict
            if schema_prop['type'] == 'dict':
                # This works if the dictionary schema is hardcoded.
                # If we define it using propertyschema and valueschema, this
                # validation pattern does not work and crahses.
                build_form(schema_prop['schema'],
                           form_prop['schema'],
                           "{0}__".format(prop_name))
                continue
            if schema_prop['type'] == 'list' and 'items' in form_prop:
                # Attempt at populating the content of a select menu. If this
                # is a large collection this will not work because of pagination.
                # This whole section should just be removed in the future. See
                # the next statement for an improved approach to this.
                for item in form_prop['items']:
                    items = eval("pillarsdk.{0}".format(item[0]))
                    items_to_select = items.all(api=api)
                    if items_to_select:
                        items_to_select = items_to_select["_items"]
                    else:
                        items_to_select = []
                    select = []
                    for select_item in items_to_select:
                        select.append((select_item['_id'], select_item[item[1]]))
                    setattr(ProceduralForm,
                            prop_name,
                            SelectMultipleField(choices=select, coerce=str))
            elif schema_prop['type'] == 'list':
                # Create and empty multiselect field, which will be populated
                # with choices from the data it's being initialized with.
                if prop == 'attachments':
                    setattr(ProceduralForm,
                            prop_name,
                            AttachmentSelectField(prop_name))
                elif prop == 'tags':
                    setattr(ProceduralForm,
                            prop_name,
                            TextField(prop_name))
                else:
                    setattr(ProceduralForm,
                            prop_name,
                            SelectMultipleField(choices=[]))
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
                        IntegerField(prop_name, default=0))
            elif schema_prop['type'] == 'float':
                setattr(ProceduralForm,
                        prop_name,
                        FloatField(prop_name, default=0))
            elif schema_prop['type'] == 'boolean':
                setattr(ProceduralForm,
                        prop_name,
                        BooleanField(prop_name))
            elif schema_prop['type'] == 'objectid' and 'data_relation' in schema_prop:
                if schema_prop['data_relation']['resource'] == 'files':
                    setattr(ProceduralForm,
                            prop_name,
                            FileSelectField(prop_name))
                else:
                    setattr(ProceduralForm,
                            prop_name,
                            TextField(prop_name))
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
        node = pillarsdk.Node.find(node_id, api=api)
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
                elif schema_prop['type'] == 'integer':
                    if data == '':
                        data = 0
                    else:
                        data = int(form[prop_name].data)
                elif schema_prop['type'] == 'datetime':
                    data = datetime.strftime(data, RFC1123_DATE_FORMAT)
                elif schema_prop['type'] == 'list':
                    if pr == 'attachments':
                        data = json.loads(data)
                    elif pr == 'tags':
                        data = [tag.strip() for tag in data.split(',')]
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
        node = pillarsdk.Node()
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
                if schema_prop['type'] == 'objectid':
                    if data == '':
                        data = None
                path = prop_name.split('__')
                if len(path) > 1:
                    prop['properties'] = recursive(path, prop['properties'], data)
                else:
                    prop['properties'][prop_name] = data

        get_data(node_schema, form_schema)

        prop['node_type'] = form.node_type_id.data
        post = node.post(prop, api=api)

        return post
