from attractsdk import utils
from attractsdk.users import User

from flask import Blueprint
from flask import render_template

from flask import flash
from flask import session
from flask import redirect
from application.modules.users.forms import UserLoginForm
from application.modules.users.forms import UserProfileForm

from application import SystemUtility

# Name of the Blueprint
users = Blueprint('users', __name__)


def authenticate(username, password):
        import requests
        import socket
        payload = dict(
            username=username,
            password=password,
            hostname=socket.gethostname())
        try:
            r = requests.post("{0}/u/identify".format(
                SystemUtility.blender_id_endpoint()), data=payload)
        except requests.exceptions.ConnectionError as e:
            raise e

        if r.status_code == 200:
            message = r.json()['message']
            if 'token' in r.json():
                authenticated = True
                token = r.json()['token']
            else:
                authenticated = False
                token = None
        else:
            message = ""
            authenticated = False
            token = None
        return dict(authenticated=authenticated, message=message, token=token)


@users.route("/login", methods=['GET', 'POST'])
def login():
    session.pop('email', None)
    session.pop('token', None)
    session.pop('user_id', None)

    form = UserLoginForm()
    if form.validate_on_submit():
        token = authenticate(form.email.data, form.password.data)['token']
        if token:
            session['email'] = form.email.data
            session['token'] = token
            # Set up api for querying about the user's ObjectId
            api = SystemUtility.attract_api()
            # We make a request with the token
            params = {'where': "token=='{0}'".format(token)}
            url = utils.join_url_params("tokens", params)
            # Since this is the first query we make with this token,
            # the id will be created during the same request.
            token = api.get(url)
            # Add the user_id to the session
            session['user_id'] = token['_items'][0]['user']

            flash('Welcome {0}!'.format(form.email.data))
            return redirect('/')
    return render_template('users/login.html', form=form)


@users.route("/logout")
def logout():
    session.pop('email', None)
    session.pop('token', None)
    session.pop('user_id', None)
    flash('Bye!')
    return redirect('/')


@users.route("/profile", methods=['GET', 'POST'])
def profile():
    """Profile view and edit page. This is a temporary implementation.
    """
    api = SystemUtility.attract_api()
    user = User.find(session['user_id'], api=api)

    form = UserProfileForm(
        first_name = user.first_name,
        last_name = user.last_name)

    if form.validate_on_submit():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.update(api=api)
        flash("Profile updated")

    return render_template('users/profile.html',
                           form=form,
                           email=SystemUtility.session_item('email'))
