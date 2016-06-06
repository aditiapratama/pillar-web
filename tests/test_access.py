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

        self.login(auth_token)

        resp = self.client.get('/',
                               headers={'Authorization': self.make_header(auth_token)})
        self.assertEqual(200, resp.status_code)
        self.assertNotIn('error', resp.data.lower())
        self.assertIn('log out', resp.data.lower())
