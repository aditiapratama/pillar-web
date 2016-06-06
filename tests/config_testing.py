"""Flask configuration file for unit testing."""

BLENDER_ID_ENDPOINT = 'http://127.0.0.1:8001'  # nonexistant server, no trailing slash!
PILLAR_SERVER_ENDPOINT = 'http://pillar:8002'  # nonexistant server, no trailing slash!
EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER = 'http://127.0.0.1:8003/'

SECRET_KEY = '12ec12ec12ec12ec'

DEBUG = False
TESTING = True

CDN_STORAGE_USER = 'u41508580125621'
CACHE_TYPE = 'null'
CACHE_NO_NULL_WARNING = True

MAIN_PROJECT_ID = 'abcdef0123456789abcdefff'
