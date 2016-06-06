# coding=utf-8
"""
Simple test to ensure some basic access rules are okay.
"""

from common_test_class import AbstractPillarWebTest


class SimpleAccessTest(AbstractPillarWebTest):
    def test_front_page_anon(self):
        """Front page should be accessible without logging in."""

        resp = self.client.get('/')
        self.assertEqual(200, resp.status_code)
        self.assertNotIn('error', resp.data.lower())
        self.assertIn('log in', resp.data.lower())

    def test_front_page_logged_in(self):
        """Front page should be accessible when logged in."""

        auth_token = 'token'

        # Log the user in
        self.mock_pillar('POST', '/auth/make-token', json={'token': auth_token})
        self.mock_pillar('GET', '/users/me', json={
            'username': 'testuser',
            '_updated': 'Mon, 06 Jun 2016 10:54:50 GMT',
            'groups': ['57305b76c379cf0b3d00a1be', '572d1e7ac379cf0b3d00951e', '573ee671c379cf134ec9ccdb'],
            'roles': ['subscriber'],
            'settings': {'email_communications': 1},
            'email': 'testuser@example.com',
            'full_name': u'Dr. Üser',
            '_created': 'Thu, 01 Jan 1970 00:00:00 GMT',
            '_id': 'aaaeeeb1c379cf10c4aaceee',
            '_etag': '0182e6e80699376ed9564b4ceaaa000f36b72317'
        })
        # Expect front-page queries.
        self.mock_pillar('GET', '/nodes', json={'_items': []})
        self.mock_pillar('GET', '/latest/assets', json={'_items': []})
        self.mock_pillar('GET', '/latest/comments', json={'_items': []})
        self.mock_pillar('GET', '/projects/abcdef0123456789abcdefff', json={})

        resp = self.client.post('/login/local', data={
            'username': 'testuser',
            'password': 'testpass',
        })
        self.assertIn(resp.status_code, {200, 302})  # render template or redirect, both fine.

        resp = self.client.get('/',
                               headers={'Authorization': self.make_header(auth_token)})
        self.assertEqual(200, resp.status_code)
        self.assertNotIn('error', resp.data.lower())
        self.assertIn('log out', resp.data.lower())
