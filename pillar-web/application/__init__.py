import sys
import os
import config
from pillarsdk import Api
from pillarsdk import NodeType
from pillarsdk.users import User
from pillarsdk.tokens import Token
from pillarsdk.exceptions import UnauthorizedAccess

from flask import Flask
from flask import session
from flask import Blueprint
from flask import redirect
from flask import url_for

from flask.ext.mail import Mail
from flask.ext.login import LoginManager
from flask.ext.login import UserMixin
from flask.ext.login import current_user

from helpers import gravatar

# Initialize the Flask all object
app = Flask(__name__,
    template_folder='templates',
    static_folder='static')

# Choose the configuration to load
app.config.from_object(config.Development)
app.config['TEMPLATES_PATH'] = '{0}/templates'.format(
    os.path.dirname(__file__))

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "users.login"
login_manager.login_message = u"Please login."


@login_manager.user_loader
def load_user(userid):
    api = Api(
        endpoint=SystemUtility.attract_server_endpoint(),
        username=None,
        password=None,
        token=userid
    )

    params = {'where': 'token=="{0}"'.format(userid)}
    token = Token.all(params, api=api)
    if token:
        user_id = token['_items'][0]['user']
        user = User.find(user_id, api=api)
    if token and user:
        login_user = userClass(userid)
        login_user.email = user['email']
        login_user.objectid = user['_id']
        login_user.username = user['username']
        #login_user.permissions = user['computed_permissions']
        login_user.gravatar = gravatar(user['email'])
        try:
            login_user.first_name = user['first_name']
        except KeyError:
            pass
        try:
            login_user.last_name = user['last_name']
        except KeyError:
            pass
    else:
        login_user = None
    return login_user


class userClass(UserMixin):
    def __init__(self, token):
        # We store the Token instead of ID
        self.id = token
        self.username = None
        self.first_name = None
        self.last_name = None
        self.objectid = None
        #self.permissions = None
        self.gravatar = None
        self.email = None


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
        is defined, we will use the one from the config object.
        """
        return os.environ.get(
            'PILLAR_SERVER_ENDPOINT', app.config['PILLAR_SERVER_ENDPOINT'])

    @staticmethod
    def attract_server_endpoint_static():
        """Endpoint to retrieve static files (previews, videos, etc)"""
        return "{0}/file_server/file/".format(SystemUtility.attract_server_endpoint())

    @staticmethod
    def attract_api():
        token = current_user.id if current_user.is_authenticated() else None
        api = Api(
            endpoint=SystemUtility.attract_server_endpoint(),
            username=None,
            password=None,
            token=token
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


# Import controllers
from application.modules.node_types import node_types
from application.modules.nodes import nodes
from application.modules.users import users
from application.modules.main import homepage
from application.helpers import url_for_other_page
from application.modules.stats import stats
from application.modules.files import files
from application.modules.organizations import organizations
from application.modules.nodes.custom import shots
from application.modules.nodes.custom import tasks
from application.modules.nodes.custom import comments

# Pagination global to use un jinja template
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

# Register blueprints for the imported controllers
app.register_blueprint(node_types, url_prefix='/node-types')
app.register_blueprint(nodes, url_prefix='/nodes')
app.register_blueprint(users, url_prefix='/users')
app.register_blueprint(stats, url_prefix='/stats')
app.register_blueprint(files, url_prefix='/files')
app.register_blueprint(organizations, url_prefix='/organizations')


@app.errorhandler(UnauthorizedAccess)
def handle_invalid_usage(error):
    """Global exception handling for pillarsdk UnauthorizedAccess
    Currently the api is fully locked down so we need to constantly
    check for user authorization.
    """
    return redirect(url_for('users.login'))


@app.context_processor
def inject_node_types():
    if current_user.is_anonymous:
        return dict(node_types={})

    api = SystemUtility.attract_api()

    types = NodeType.all(api=api)['_items']
    node_types = []
    for t in types:
        # If we need to include more info, we can turn node_types into a dict
        # node_types[t.name] = dict(
        #     url_view=url_for('nodes.index', node_type_name=t.name))
        node_types.append(str(t['name']))

    return dict(node_types=node_types)
