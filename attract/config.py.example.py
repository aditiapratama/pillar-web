import os

class Config(object):
    # Configured for GMAIL
    MAIL_SERVER = ''
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    DEFAULT_MAIL_SENDER = ''


class Development(Config):
    SECRET_KEY=''
    #SERVER_NAME='attract.local:5555'
    ATTRACT_SERVER='http://127.0.0.1:5000'
    HOST='0.0.0.0'
    PORT=5001
    DEBUG=True
    SQLALCHEMY_DATABASE_URI=''
    SECURITY_REGISTERABLE=True
    SECURITY_LOGIN_USER_TEMPLATE = 'security/login_user.html'
    MEDIA_FOLDER = ''
    MEDIA_URL = ''
    MEDIA_THUMBNAIL_FOLDER = ''
    MEDIA_THUMBNAIL_URL = ''
    FILE_STORAGE = '{0}/application/static/storage'.format(
                os.path.join(os.path.dirname(__file__)))
    FILE_STORAGE_BACKEND = 'attract'
