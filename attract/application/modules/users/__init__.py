from flask import Blueprint
from flask import render_template

from flask import flash
from flask import redirect
from application.modules.users.forms import UserLoginForm


# Name of the Blueprint
users = Blueprint('users', __name__)

@users.route("/login", methods=['GET', 'POST'])
def login():
    form = UserLoginForm()
    if form.validate_on_submit():
        flash('Welcome!')
        return redirect('/')
    return render_template('users/login.html',
                           form=form)

