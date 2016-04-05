import os

from application import app
from flask.ext.script import Manager

manager = Manager(app)


@manager.command
def runserver():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
    app.run(host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'])


manager.run()
