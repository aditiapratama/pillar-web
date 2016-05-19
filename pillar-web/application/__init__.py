import flask_login
import os
import logging
import logging.config
import config
import bugsnag
import redis
from bugsnag.flask import handle_exceptions
from pillarsdk import Api
from pillarsdk import NodeType
from pillarsdk.users import User
from pillarsdk.tokens import Token
from pillarsdk import exceptions as sdk_exceptions

from flask import Flask
from flask import session
from flask import redirect
from flask import url_for
from flask_oauthlib.client import OAuth

from flask.ext.login import LoginManager
from flask.ext.login import UserMixin
from flask.ext.login import current_user
from flask.ext.cache import Cache

# Initialize the Flask all object
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Load configuration from three different sources, to make it easy to override
# settings with secrets, as well as for development & testing.
app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.config.from_pyfile(os.path.join(app_root, 'config.py'), silent=False)
app.config.from_pyfile(os.path.join(app_root, 'config_local.py'), silent=True)
from_envvar = os.environ.get('PILLAR_WEB_CONFIG')
if from_envvar:
    # Don't use from_envvar, as we want different behaviour. If the envvar
    # is not set, it's fine (i.e. silent=True), but if it is set and the
    # configfile doesn't exist, it should error out (i.e. silent=False).
    app.config.from_pyfile(from_envvar, silent=False)

# Configure logging
logging.config.dictConfig(app.config['LOGGING'])
log = logging.getLogger(__name__)
log.info('Pillar Web starting')

# Configure Bugsnag
if not app.config.get('TESTING'):
    bugsnag.configure(
        api_key=app.config['BUGSNAG_API_KEY'],
        project_root="/data/dev/pillar-web/pillar-web",
    )

    def bugsnag_notify_callback(notification):
        # If we return False, the notification will not be sent to Bugsnag.
        if isinstance(notification.exception, KeyboardInterrupt):
            return False
        if current_user.is_authenticated():
            notification.user = dict(
                id=current_user.id,
                name=current_user.full_name,
                email=current_user.email)
            notification.add_tab("account", {"roles": current_user.roles})

    bugsnag.before_notify(bugsnag_notify_callback)
    handle_exceptions(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "users.login"
login_manager.login_message = u''


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
        login_user = UserClass(userid)
        login_user.email = user.email
        login_user.objectid = user._id
        login_user.username = user.username
        login_user.gravatar = gravatar(user.email)
        login_user.roles = user.roles
        login_user.groups = user.groups
        try:
            login_user.full_name = user.full_name
        except KeyError:
            pass
    else:
        login_user = None
    return login_user

# Set up authentication
oauth = OAuth(app)
if app.config.get('SOCIAL_BLENDER_ID'):
    blender_id = oauth.remote_app(
        'blender_id',
        consumer_key=app.config.get('SOCIAL_BLENDER_ID')['app_id'],
        consumer_secret=app.config.get('SOCIAL_BLENDER_ID')['app_secret'],
        request_token_params={'scope': 'email'},
        base_url=app.config['BLENDER_ID_OAUTH_URL'],
        request_token_url=None,
        access_token_url=app.config['BLENDER_ID_BASE_ACCESS_TOKEN_URL'],
        authorize_url=app.config['BLENDER_ID_AUTHORIZE_URL']
    )
else:
    blender_id = None


class UserClass(UserMixin):
    def __init__(self, token):
        # We store the Token instead of ID
        self.id = token
        self.username = None
        self.full_name = None
        self.objectid = None
        self.gravatar = None
        self.email = None
        self.roles = []

    def has_role(self, *roles):
        """Returns True iff the user has one or more of the given roles."""

        if not self.roles:
            return False

        return bool(set(self.roles).intersection(set(roles)))


class AnonymousUserMixin(flask_login.AnonymousUserMixin):
    def has_role(self, *roles):
        return False


login_manager.anonymous_user = AnonymousUserMixin


class SystemUtility():
    def __new__(cls, *args, **kwargs):
        raise TypeError("Base class may not be instantiated")

    @staticmethod
    def blender_id_endpoint():
        """Gets the endpoint for the authentication API. If the env variable
        is defined, it's possible to override the (default) production address.
        """
        return os.environ.get(
            'BLENDER_ID_ENDPOINT', "https://www.blender.org/id").rstrip('/')

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
        token = None
        # Check if current_user is initialized (in order to support manage.py
        # scripts and non authenticated server requests).
        if current_user and current_user.is_authenticated():
            token = current_user.id
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

# Initialize the available extensions
cache = Cache(app)

# Initialize Redis client to manage deletion of custom cache keys
if app.config.get('CACHE_REDIS_HOST') and app.config['CACHE_TYPE'] == 'redis':
    redis_client = redis.StrictRedis(
        host=app.config['CACHE_REDIS_HOST'],
        port=app.config['CACHE_REDIS_PORT'])
else:
    redis_client = None


# Import controllers
from modules.node_types import node_types
from modules.nodes import nodes
from modules.users import users
from helpers import url_for_other_page
from modules.stats import stats
from modules.files import files
from modules.organizations import organizations
from modules.projects import projects
from modules.projects import create as create_project
from modules.nodes.custom import comments
from modules.notifications import notifications
from modules.main import homepage
from helpers import gravatar
from helpers import pretty_date
from helpers import get_main_project

get_main_project()


@app.template_filter('pretty_date')
def format_pretty_date(d):
    return pretty_date(d)

# Pagination global to use un Jinja template
app.jinja_env.globals['url_for_other_page'] = url_for_other_page

# Register blueprints for the imported controllers
app.register_blueprint(node_types, url_prefix='/node-types')
app.register_blueprint(nodes, url_prefix='/nodes')
app.register_blueprint(users)
app.register_blueprint(stats, url_prefix='/stats')
app.register_blueprint(files, url_prefix='/files')
app.register_blueprint(organizations, url_prefix='/organizations')
app.register_blueprint(projects, url_prefix='/p')
app.register_blueprint(notifications, url_prefix='/notifications')


@app.errorhandler(sdk_exceptions.UnauthorizedAccess)
def handle_invalid_usage(error):
    """Global exception handling for pillarsdk UnauthorizedAccess
    Currently the api is fully locked down so we need to constantly
    check for user authorization.
    """
    return redirect(url_for('users.login'))


@app.errorhandler(sdk_exceptions.ForbiddenAccess)
def handle_sdk_forbidden(error):
    from werkzeug.exceptions import Forbidden
    log.info('Forwarding ForbiddenAccess exception to client: %s', error)
    raise Forbidden()


@app.errorhandler(sdk_exceptions.ResourceNotFound)
def handle_sdk_resource_not_found(error):
    from werkzeug.exceptions import NotFound
    log.info('Forwarding ResourceNotFound exception to client: %s', error)
    raise NotFound()


@app.errorhandler(sdk_exceptions.ResourceInvalid)
def handle_sdk_resource_invalid(error):
    log.info('Forwarding ResourceInvalid exception to client: %s', error)

    # Raising a Werkzeug 422 exception doens't work, as Flask turns it into a 500.
    return 'The submitted data could not be validated.', 422
