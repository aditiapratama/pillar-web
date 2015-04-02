import config
from flask import Flask, Blueprint
from flask.ext.mail import Mail
# from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.thumbnails import Thumbnail
from flask.ext.assets import Environment

from attractsdk import Api as attractsdk

# Initialize the Flask all object
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Filemanager used by Flask-Admin extension
filemanager = Blueprint('filemanager', __name__, static_folder='static/files')

# Choose the configuration to load
app.config.from_object(config.Development)

# Initialized the available extensions
mail = Mail(app)
attractsdk.Default(
    endpoint='http://127.0.0.1:5000',
    username="admin",
    password="secret"
)
thumb = Thumbnail(app)
assets = Environment(app)

# Import controllers
from application.modules.node_types import node_types
from application.modules.nodes import nodes
from application.modules.users import users
from application.modules.main import homepage

# Register blueprints for the imported controllers
app.register_blueprint(filemanager)
app.register_blueprint(node_types, url_prefix='/node-types')
app.register_blueprint(nodes, url_prefix='/nodes')
app.register_blueprint(users, url_prefix='/users')
