from os.path import join, dirname, abspath

TEMPLATES_PATH = join(dirname(abspath(__file__)), 'application/templates')
RFC1123_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

# Uploader settings
MAX_CONTENT_LENGTH = 10 * 1024 ** 3  # In bytes
ALLOWED_EXTENSIONS = {'tif', 'tiff', 'exr', 'm4v', 'kra', 'xcf', 'avi', 'blend', 'zip', 'txt', 'gif', 'png', 'jpg',
                      'jpeg', 'bmp', 'mov', 'mp4', 'pdf'}
IGNORED_FILES = {'.gitignore'}

SCHEME = 'https'
SECRET_KEY = '123'
PILLAR_SERVER_ENDPOINT = 'http://pillar:5000'
HOST = '0.0.0.0'
PORT = 5001
DEBUG = False
SECURITY_REGISTERABLE = True

STORAGE_DIR = '/data/storage/pillar-web/storage'
UPLOAD_DIR = '/data/storage/pillar-web/uploads'
SHARED_DIR = '/data/storage/shared'
FLOWPLAYER_KEY = '-SECRET-'

MAIN_PROJECT_ID = '-SYSTEM-SPECIFIC-'

EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER = 'https://store.blender.org/api/'

BUGSNAG_API_KEY = ''

CACHE_TYPE = 'redis'  # null
CACHE_KEY_PREFIX = 'pw'
CACHE_REDIS_HOST = 'redis_pillar_web'
CACHE_REDIS_PORT = '6379'
CACHE_REDIS_URL = 'redis://redis_pillar_web:6379'

GOOGLE_ANALYTICS_TRACKING_ID = ''

ALGOLIA_USER = '-SECRET-'
ALGOLIA_PUBLIC_KEY = '-SECRET-'
ALGOLIA_INDEX_USERS = 'dev_Users'

SOCIAL_BLENDER_ID = {
    'app_id': '-SECRET-',
    'app_secret': '-SECRET-'
}
BLENDER_ID_BASE_URL = 'http://blender_id:8000/'
# BLENDER_ID_BASE_URL = 'https://www.blender.org/id/'
BLENDER_ID_OAUTH_URL = BLENDER_ID_BASE_URL + 'api/'
BLENDER_ID_BASE_ACCESS_TOKEN_URL = BLENDER_ID_BASE_URL + 'oauth/token'
BLENDER_ID_AUTHORIZE_URL = BLENDER_ID_BASE_URL + 'oauth/authorize'

# See https://docs.python.org/2/library/logging.config.html#configuration-dictionary-schema
LOGGING = {
    'version': 1,
    'formatters': {
        'default': {'format': '%(asctime)-15s %(levelname)8s %(name)s %(message)s'}
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stderr',
        }
    },
    'loggers': {
        'application': {'level': 'INFO'},
    },
    'root': {
        'level': 'WARNING',
        'handlers': [
            'console',
        ],
    }
}
