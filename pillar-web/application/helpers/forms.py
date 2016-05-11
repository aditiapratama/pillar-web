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
    def __init__(self, file_format=None, **kwargs):
        super(CustomFileSelectWidget, self).__init__(**kwargs)
        self.file_format = file_format

    def __call__(self, field, **kwargs):
        html = super(CustomFileSelectWidget, self).__call__(field, **kwargs)

        file_format = self.file_format
        file_format_regex = ''
        if file_format and file_format == 'image':
            file_format_regex = '^image\/(gif|jpe?g|png|tif?f|tga)$'

        button = '<div class="form-upload-file">'

        if field.data:
            api = SystemUtility.attract_api()
            try:
                # Load the existing file attached to the field
                file_item = File.find(field.data, api=api)
            except ResourceNotFound:
                pass
            else:
                filename = Markup.escape(file_item.filename)
                if file_item.content_type.split('/')[0] == 'image':
                    # If a file of type image is available, display the preview
                    button += '<img class="preview-thumbnail" ' \
                              'src="{0}" />'.format(
                               file_item.thumbnail('s', api=api))
                else:
                    button += '<p>{}</p>'.format(filename)

                button += '<ul class="form-upload-file-meta">'
                # File name
                button += '<li class="name">{0}</li>'.format(filename)
                # File size
                button += '<li class="size">({0} MB)</li>'.format(
                           round((file_item.length/1024)*0.001, 2))
                # Image resolution (if image)
                button += '<li class="dimensions">{0}x{1}</li>'.format(
                          file_item.width, file_item.height)
                # Delete button
                button += '<li class="delete">' \
                          '<a href="#" class="file_delete" ' \
                          'data-field-name="{field_name}" ' \
                          'data-file_id="{file_id}"> ' \
                          '<i class="pi-trash"></i> Delete</a></li>'.format(
                           field_name=field.name, file_id=field.data)
                # Download button for original file
                button += '<li class="original">' \
                          '<a href="{}" class="file_original"> ' \
                          '<i class="pi-download"></i>Original</a></li>'.format(
                           file_item.link)
                button += '</ul>'

        upload_url = '%s/storage/stream/{project_id}' % current_app.config['PILLAR_SERVER_ENDPOINT']

        button += '<input class="fileupload" type="file" name="file" ' \
                  'data-url="{url}" ' \
                  'data-field-name="{name}" ' \
                  'data-token="{token}" ' \
                  'data-file-format="{file_format}">' \
                  '<div class="form-upload-progress"> ' \
                  '<div class="form-upload-progress-bar" role="progressbar" ' \
                  'aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" ' \
                  'style="width: 0%;"> ' \
                  '</div> ' \
                  '</div>'.format(
                   url=upload_url,
                   name=field.name,
                   token=Markup.escape(current_user.id),
                   file_format=Markup.escape(file_format_regex))

        button += '</div>'

        return HTMLString(html + button)


class FileSelectField(StringField):
    def __init__(self, name, file_format=None, **kwargs):
        super(FileSelectField, self).__init__(name, **kwargs)
        self.widget = CustomFileSelectWidget(file_format=file_format)


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
            if 'allowed' in field_schema:
                choices = [(c, c) for c in field_schema['allowed']]
                field = SelectField(choices=choices)
            else:
                field = StringField()
        elif field_schema['type'] == 'objectid':
            field = FileSelectField('file')
        else:
            raise ValueError('field type %s not supported' % field_schema['type'])

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
