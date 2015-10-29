from flask_wtf import Form
from wtforms import TextField
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms.validators import DataRequired


class UserLoginForm(Form):
    email = TextField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(UserLoginForm, self).__init__(csrf_enabled=False, *args, **kwargs)


class UserProfileForm(Form):
    full_name = TextField('Full Name', validators=[DataRequired()])

    def __init__(self, csrf_enabled=False, *args, **kwargs):
        super(UserProfileForm, self).__init__(csrf_enabled=False, *args, **kwargs)
