import sys
import os
import config
from attractsdk import Api
from attractsdk.exceptions import UnauthorizedAccess

from flask import Flask
from flask import session
from flask import Blueprint
from flask import redirect
from flask import url_for

from flask.ext.mail import Mail
from flask.ext.thumbnails import Thumbnail
from flask.ext.assets import Environment


# Initialize the Flask all object
app = Flask(__name__,
    template_folder='templates',
    static_folder='static')

# Filemanager used by Flask-Admin extension
filemanager = Blueprint('filemanager', __name__, static_folder='static/files')

# Choose the configuration to load
app.config.from_object(config.Development)

class SystemUtility():
    def __new__(cls, *args, **kwargs):
        raise TypeError("Base class may not be instantiated")

    @staticmethod
    def blender_id_endpoint():
        """Gets the endpoint for the authentication API. If the env variable
        is defined, it's possible to override the (default) production address.
        """
        return os.environ.get(
            'BLENDER_ID_ENDPOINT', "https://www.blender.org/id")

    @staticmethod
    def attract_server_endpoint():
        """Gets the endpoint for the authentication API. If the env variable
        is defined, it's possible to override the (default) production address.
        """
        return os.environ.get(
            'ATTRACT_SERVER_ENDPOINT', "http://127.0.0.1:5000")

    @staticmethod
    def attract_api():
        api = Api(
            endpoint=SystemUtility.attract_server_endpoint(),
            username=None,
            password=None,
            token=SystemUtility.session_item('token')
        )
        return api

    @staticmethod
    def session_item(item):
        if item in session:
            return session[item]
        else:
            return None

# Initialized the available extensions
mail = Mail(app)
thumb = Thumbnail(app)
assets = Environment(app)


# Import controllers
from application.modules.node_types import node_types
from application.modules.nodes import nodes
from application.modules.users import users
from application.modules.main import homepage
from application.helpers import url_for_other_page
from application.modules.stats import stats

# Pagination global to use un jinja template
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

# Register blueprints for the imported controllers
app.register_blueprint(filemanager)
app.register_blueprint(node_types, url_prefix='/node-types')
app.register_blueprint(nodes, url_prefix='/nodes')
app.register_blueprint(users, url_prefix='/users')
app.register_blueprint(stats, url_prefix='/stats')


@app.errorhandler(UnauthorizedAccess)
def handle_invalid_usage(error):
    """Global exception handling for attractsdk UnauthorizedAccess
    Currently the api is fully locked down so we need to constantly
    check for user authorization.
    """
    return redirect(url_for('users.login'))
