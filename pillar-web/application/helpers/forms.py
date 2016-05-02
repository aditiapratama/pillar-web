from markupsafe import Markup

from pillarsdk import File
from flask import current_app
from flask.ext.login import current_user
from wtforms import Form
from wtforms import StringField
from wtforms import DateField
from wtforms import SelectField
from wtforms import HiddenField
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import FloatField
from wtforms import TextAreaField
from wtforms import DateTimeField
from wtforms import SelectMultipleField
from wtforms.fields import FileField
from wtforms.compat import text_type
from wtforms.widgets import html_params
from wtforms.widgets import HiddenInput
from wtforms.widgets import HTMLString
from wtforms.fields import FormField
from pillarsdk.exceptions import ResourceNotFound
from application import SystemUtility


class CustomFileSelectWidget(HiddenInput):
    def __init__(self, **kwargs):
        super(CustomFileSelectWidget, self).__init__(**kwargs)

    def __call__(self, field, **kwargs):
        html = super(CustomFileSelectWidget, self).__call__(field, **kwargs)

        button = '<div class="form-upload-file">'

        if field.data:
            api = SystemUtility.attract_api()
            try:
                file_item = File.find(field.data, api=api)

                filename = Markup.escape(file_item.filename)
                if file_item.content_type.split('/')[0] == 'image':
                    button += '<img class="preview-thumbnail" src="{0}" />'.format(
                        file_item.thumbnail('s', api=api))
                else:
                    button += '<p>{}</p>'.format(filename)
                button += '<ul class="form-upload-file-meta">'
                button += '<li class="name">{0}</li>'.format(filename)
                button += '<li class="size">({0} MB)</li>'.format(round((file_item.length/1024)*0.001, 2))
                button += '<li class="dimensions">{0}x{1}</li>'.format(file_item.width, file_item.height)
                button += '<li class="delete"><a href="#" class="file_delete" data-field-name="{1}" \
                    data-file_id="{0}"> <i class="pi-trash"></i> Delete</a></li>'.format(field.data, field.name)
                button += '<li class="original"><a href="{}" class="file_original"> <i class="pi-download"></i>Original</a></li>'.format(
                    file_item.link)
                button += '</ul>'
            except ResourceNotFound:
                pass

        upload_url = '%s/storage/stream/{project_id}' % current_app.config['PILLAR_SERVER_ENDPOINT']

        button += """
        <input class="fileupload" type="file" name="file" data-url="{0}" data-field-name="{1}" data-token="{2}">
        <div class="form-upload-progress">
          <div class="form-upload-progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;">
          </div>
        </div>""".format(upload_url, field.name, Markup.escape(current_user.id))

        button += '</div>'

        return HTMLString(html + button)


class FileSelectField(StringField):
    def __init__(self, name, **kwargs):
        super(FileSelectField, self).__init__(name, **kwargs)
        self.widget = CustomFileSelectWidget()


class ProceduralFileSelectForm(Form):
    file = FileSelectField('file')
    size = StringField()
    slug = StringField()


def build_file_select_form(schema):
    class FileSelectForm(Form):
        pass
    for field_name, field_schema in schema.iteritems():
        if field_schema['type'] == 'boolean':
            field = BooleanField()
        elif field_schema['type'] == 'string':
            field = StringField()
            if 'allowed' in field_schema:
                choices = [(c, c) for c in field_schema['allowed']]
                field.choices = choices
        elif field_schema['type'] == 'objectid':
            FileSelectField('file')

        setattr(FileSelectForm, field_name, field)
    return FileSelectForm


class CustomFormFieldWidget(object):
    """
    Renders a list of fields as in the way we like. Based the TableWidget.

    Hidden fields will not be displayed with a row, instead the field will be
    pushed into a subsequent table row to ensure XHTML validity. Hidden fields
    at the end of the field list will appear outside the table.
    """
    def __call__(self, field, **kwargs):
        html = []
        kwargs.setdefault('id', field.id)
        html.append('<div %s>' % html_params(**kwargs))
        hidden = ''
        for subfield in field:
            if subfield.type == 'HiddenField':
                hidden += text_type(subfield)
            else:
                html.append('<div><span>%s</span>%s%s</div>' % (
                    text_type(subfield.label), hidden, text_type(subfield)))
                hidden = ''
        html.append('</div>')
        if hidden:
            html.append(hidden)
        return HTMLString(''.join(html))


class CustomFormField(FormField):
    def __init__(self, name, **kwargs):
        super(CustomFormField, self).__init__(name, **kwargs)
        self.widget = CustomFormFieldWidget()
