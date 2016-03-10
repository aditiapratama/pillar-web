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

        button = ""
        if field.data:
            api = SystemUtility.attract_api()
            try:
                picture = File.find(field.data, api=api)
                button += '<img class="preview-thumbnail" src="{0}" />'.format(
                    picture.thumbnail('s', api=api))
                button += '<a href="#" class="file_delete" data-field-name="{1}" \
                    data-file_id="{0}"> Delete</a>'.format(field.data, field.name)
                button += '<a href="{}" class="file_original">Original</a>'.format(
                    picture.link)
            except ResourceNotFound:
                pass

        button += """
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
