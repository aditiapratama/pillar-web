from pillarsdk.users import User
from pillarsdk.projects import Project
from flask.ext.login import current_user
from flask_wtf import Form
from wtforms import StringField
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import RadioField
from wtforms import HiddenField
from wtforms import TextAreaField
from wtforms import SelectField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import NoneOf
from wtforms.validators import Regexp
from application import SystemUtility
from application.helpers.forms import FileSelectField


class ProjectForm(Form):
    project_id = HiddenField('project_id', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    url = StringField('Url', validators=[DataRequired()])
    summary = StringField('Summary', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    is_private = BooleanField('Private')
    category = SelectField('Category', choices=[
        ('film', 'Film'), ('training', 'Training'), ('assets', 'Assets')])
    status = SelectField('Status', choices=[
        ('published', 'Published'), ('pending', 'Pending'), ('deleted', 'Deleted')])
    picture_header = FileSelectField('Picture header')
    picture_square = FileSelectField('Picture square')

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        api = SystemUtility.attract_api()
        project = Project.find(self.project_id.data, api=api)
        if project.url != self.url.data:
            project_url = Project.find_one({'where': '{"url": "%s"}' % (self.url.data)},
                api=api)
            if project_url:
                self.url.errors.append('Sorry, project url already exists!')
                return False
        return True

    # def __init__(self, csrf_enabled=False, *args, **kwargs):
    #     super(ProjectForm, self).__init__(csrf_enabled=False, *args, **kwargs)

class NodeTypeForm(Form):
    project_id = HiddenField('project_id', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    parent = StringField('Parent')
    description = TextAreaField('Description')
    dyn_schema = TextAreaField('Schema', validators=[DataRequired()])
    form_schema = TextAreaField('Form Schema', validators=[DataRequired()])
    permissions = TextAreaField('Permissions', validators=[DataRequired()])
