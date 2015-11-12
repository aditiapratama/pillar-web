from pillarsdk.users import User
from flask_wtf import Form
from wtforms import StringField
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import RadioField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import NoneOf
from wtforms.validators import Regexp
from application import SystemUtility


class UserLoginForm(Form):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(UserLoginForm, self).__init__(csrf_enabled=False, *args, **kwargs)


class UserProfileForm(Form):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(
        min=3, max=128, message="Min. 3 and max. 128 chars please")])
    username = StringField('Username', validators=[DataRequired(), Length(
        min=3, max=128, message="Min. 3, max. 128 chars please"), Regexp(
        r'^[\w.@+-]+$', message="Please do not use spaces")])

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(UserProfileForm, self).__init__(csrf_enabled=False, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        api = SystemUtility.attract_api()
        user = User.find_first({'where': '{"username": "%s"}' % (self.username.data)}, api=api)

        if user:
            self.username.errors.append('Sorry, username already exists!')
            return False

        self.user = user
        return True


class UserSettingsEmailsForm(Form):
    choices = [(1, 'Receive all emails, except those I unsubscribe from.'),
        (0, 'Only receive account related emails.')]
    email_communications = RadioField('Notifications', choices=choices, coerce=int)
