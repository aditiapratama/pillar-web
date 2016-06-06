# -*- encoding: utf-8 -*-

import sys
import logging
import os
import base64
import unittest

from flask.testing import FlaskClient
import responses

MY_PATH = os.path.dirname(os.path.abspath(__file__))

# We require this even before the entire application is started,
# so we can't take it from self.app.config['....']
PILLAR_SERVER_ENDPOINT = 'http://pillar:8002'  # nonexistant server, no trailing slash!

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)-15s %(levelname)8s %(name)s %(message)s')


class AbstractPillarWebTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.responses = responses.RequestsMock()

    def setUp(self):
        pillar_web_config_file = os.path.join(MY_PATH, 'config_testing.py')
        os.environ['PILLAR_WEB_CONFIG'] = pillar_web_config_file

        self.responses.start()
        self.mock_pillar('GET', '/projects/abcdef0123456789abcdefff', json={})

        from application import app

        self.app = app
        self.client = app.test_client()
        assert isinstance(self.client, FlaskClient)

    def tearDown(self):
        del self.client
        del self.app
        del sys.modules['application']

        # Also unload submodules.
        to_rm = [name for name in sys.modules if name.startswith('application.')]
        for name in to_rm:
            del sys.modules[name]

        self.responses.stop()
        self.responses.reset()

    def make_header(self, username, subclient_id=''):
        """Returns a Basic HTTP Authentication header value."""

        return 'basic ' + base64.b64encode('%s:%s' % (username, subclient_id))

    def mock_pillar(self, method, url, body='', match_querystring=False,
                    status=200, adding_headers=None, stream=False,
                    content_type='text/plain', json=None):
        """Mock a call to pillar."""

        abs_url = '%s%s' % (PILLAR_SERVER_ENDPOINT, url)
        self.responses.add(method=method,
                           url=abs_url,
                           body=body,
                           match_querystring=match_querystring,
                           status=status,
                           adding_headers=adding_headers,
                           stream=stream,
                           content_type=content_type,
                           json=json)
