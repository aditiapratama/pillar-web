from application import app
from flask.ext.script import Manager

manager = Manager(app)


@manager.command
def runserver():
    try:
        import config
        PORT = config.Development.PORT
        HOST = config.Development.HOST
        DEBUG = config.Development.DEBUG
    except:
        PORT = 5001
        HOST = '0.0.0.0'
        DEBUG = True
    app.run(port=PORT,
            host=HOST,
            debug=DEBUG)

manager.run()
