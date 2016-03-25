from pillarsdk import File
from flask import url_for
from wtforms import TextField
from wtforms.widgets import HiddenInput
from wtforms.widgets import HTMLString
from pillarsdk.exceptions import ResourceNotFound
from application import SystemUtility


class FileSelectText(HiddenInput):
    def __init__(self, **kwargs):
        super(FileSelectText, self).__init__(**kwargs)

    def __call__(self, field, **kwargs):
        html = super(FileSelectText, self).__call__(field, **kwargs)

        button = '<div class="form-upload-file">'

        if field.data:
            api = SystemUtility.attract_api()
            try:
                file_item = File.find(field.data, api=api)

                if file_item.content_type.split('/')[0] == 'image':
                    button += '<img class="preview-thumbnail" src="{0}" />'.format(
                        file_item.thumbnail('s', api=api))
                else:
                    button += '<p>{}</p>'.format(file_item.filename)
                button += '<ul class="form-upload-file-meta">'
                button += '<li class="name">{0}</li>'.format(file_item.filename)
                button += '<li class="size">({0} MB)</li>'.format(round((file_item.length/1024)*0.001, 2))
                button += '<li class="dimensions">{0}x{1}</li>'.format(file_item.width, file_item.height)
                button += '<li class="delete"><a href="#" class="file_delete" data-field-name="{1}" \
                    data-file_id="{0}"> <i class="pi-trash"></i> Delete</a></li>'.format(field.data, field.name)
                button += '<li class="original"><a href="{}" class="file_original"> <i class="pi-download"></i>Original</a></li>'.format(
                    file_item.link)
                button += '</ul>'
            except ResourceNotFound:
                pass

        button += """
        <input class="fileupload" type="file" name="file" data-url="{0}" data-field-name="{1}">
        <div class="form-upload-progress">
          <div class="form-upload-progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;">
          </div>
        </div>""".format(url_for('files.upload'), field.name)

        button += '</div>'

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
        <div class="form-upload-progress">
          <div class="form-upload-progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;">
          </div>
        </div>""".format(url_for('files.upload'), field.name)
        return HTMLString(html + button)


class AttachmentSelectField(TextField):
    def __init__(self, name, **kwargs):
        super(AttachmentSelectField, self).__init__(name, **kwargs)
        self.widget = FileSelectAttachment()
