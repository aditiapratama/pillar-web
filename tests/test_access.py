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

        self.expect_frontpage_queries()
        resp = self.client.get('/',
                               headers={'Authorization': self.make_header(auth_token)})
        self.assertEqual(200, resp.status_code)
        self.assertNotIn('error', resp.data.lower())
        self.assertIn('log out', resp.data.lower())

    def test_video_anon(self):
        """Video page should be accessible when not logged in, but video itself should not."""

        link_to_webm = 'https://storage.googleapis.com/LINK-TO-WEBM'
        link_to_mp4 = 'https://storage.googleapis.com/LINK-TO-MP4'
        link_to_file = 'https://storage.googleapis.com/LINK-TO-FILE'

        self._mock_node_get(link_to_mp4, link_to_webm, link_to_file)

        resp = self.client.get('/nodes/56e3a51ac379cf26b1cd877a/view')
        self.assertEqual(200, resp.status_code)
        self.assertNotIn(link_to_mp4, resp.data)
        self.assertNotIn(link_to_webm, resp.data)
        self.assertNotIn(link_to_file, resp.data)

    def test_video_logged_in(self):
        """Video page should be accessible when not logged in, but video itself should not."""

        link_to_webm = 'https://storage.googleapis.com/LINK-TO-WEBM'
        link_to_mp4 = 'https://storage.googleapis.com/LINK-TO-MP4'
        link_to_file = 'https://storage.googleapis.com/LINK-TO-FILE'

        self._mock_node_get(link_to_mp4, link_to_webm, link_to_file)

        auth_token = 'token'
        self.login(auth_token)
        resp = self.client.get('/nodes/56e3a51ac379cf26b1cd877a/view',
                               headers={'Authorization': self.make_header(auth_token)})
        self.assertEqual(200, resp.status_code)
        self.assertIn(link_to_mp4, resp.data)
        self.assertIn(link_to_webm, resp.data)
        self.assertNotIn(link_to_file, resp.data)

    def test_video_public_anon(self):
        """Video page should be accessible when not logged in, but video itself should not."""

        link_to_webm = 'https://storage.googleapis.com/LINK-TO-WEBM'
        link_to_mp4 = 'https://storage.googleapis.com/LINK-TO-MP4'
        link_to_file = 'https://storage.googleapis.com/LINK-TO-FILE'

        self._mock_node_get(link_to_mp4, link_to_webm, link_to_file,
                            {'permissions': {'world': ['GET']}})

        resp = self.client.get('/nodes/56e3a51ac379cf26b1cd877a/view')
        self.assertEqual(200, resp.status_code)
        self.assertIn(link_to_mp4, resp.data)
        self.assertIn(link_to_webm, resp.data)
        self.assertNotIn(link_to_file, resp.data)

    def test_video_public_logged_in(self):
        """Video page should be accessible when not logged in, but video itself should not."""

        link_to_webm = 'https://storage.googleapis.com/LINK-TO-WEBM'
        link_to_mp4 = 'https://storage.googleapis.com/LINK-TO-MP4'
        link_to_file = 'https://storage.googleapis.com/LINK-TO-FILE'

        self._mock_node_get(link_to_mp4, link_to_webm, link_to_file,
                            {'permissions': {'world': ['GET']}})

        auth_token = 'token'
        self.login(auth_token)
        resp = self.client.get('/nodes/56e3a51ac379cf26b1cd877a/view',
                               headers={'Authorization': self.make_header(auth_token)})
        self.assertEqual(200, resp.status_code)
        self.assertIn(link_to_mp4, resp.data)
        self.assertIn(link_to_webm, resp.data)
        self.assertNotIn(link_to_file, resp.data)

    def _mock_node_get(self, link_to_mp4, link_to_webm, link_to_file, node_override=None):
        node = {'_created': 'Sat, 12 Mar 2016 05:11:54 GMT',
                '_deleted': False,
                '_etag': 'd7c7231cc31d3ba0e0e6d8266701586ec613c880',
                '_id': '56e3a51ac379cf26b1cd877a',
                '_updated': 'Tue, 15 Mar 2016 20:50:51 GMT',
                'allowed_methods': ['GET'],
                'description': '**RE-TARGETING THE BODY**\n\nLearn how to ...', 'name': 'BlenRig 5 T01 - Ch01',
                'node_type': 'asset',
                'parent': None,
                'permissions': {},
                'picture': None,
                'project': '565dbae36dcaf85da2faef3e',
                'properties': {'categories': '',
                               'content_type': 'video',
                               'file': '56e3a519c379cf26b1cd8779',
                               'order': 0,
                               'status': 'published',
                               'tags': []},
                'user': '56354417c379cf012919cc8b'}
        if node_override:
            node.update(node_override)

        self.mock_pillar('GET', '/nodes/56e3a51ac379cf26b1cd877a', json=node)
        self.mock_pillar('GET', '/files/56e3a519c379cf26b1cd8779', json={
            '_created': 'Sat, 12 Mar 2016 05:11:53 GMT',
            '_etag': '9c3e9278b51f7f03429d732af17b23dca8e007a5',
            '_id': '56e3a519c379cf26b1cd8779',
            '_updated': 'Mon, 06 Jun 2016 04:13:47 GMT',
            'backend': 'gcs',
            'content_type': 'video/m4v',
            'duration': 522,
            'file_path': '45144c435e42291a14fafd5f0737b8cbd7a1ba59.m4v',
            'filename': 'blenrig_tutorial_01_chapter_01_audio.m4v',
            'format': 'm4v',
            'length': 254876752,
            'length_aggregate_in_bytes': 434605799,
            'link': 'https://storage.googleapis.com/LINK-TO-FILE',
            'link_expires': 'Tue, 07 Jun 2016 03:13:46 GMT',
            'md5': '',
            'name': '45144c435e42291a14fafd5f0737b8cbd7a1ba59.m4v',
            'processing': {
                'backend': 'zencoder',
                'job_id': '242860926',
                'status': 'finished'
            },
            'project': '565dbae36dcaf85da2faef3e',
            'user': '56354417c379cf012919cc8b',
            'variations': [
                {
                    'content_type': 'video/mp4',
                    'duration': 522,
                    'file_path': '45144c435e42291a14fafd5f0737b8cbd7a1ba59-1080p.mp4',
                    'format': 'mp4',
                    'height': 1200,
                    'length': 88470119,
                    'link': link_to_mp4,
                    'md5': '',
                    'size': '1080p',
                    'width': 1920
                },
                {
                    'content_type': 'video/webm',
                    'duration': 522,
                    'file_path': '45144c435e42291a14fafd5f0737b8cbd7a1ba59-1080p.webm',
                    'format': 'webm',
                    'height': 1200,
                    'length': 91258928,
                    'link': link_to_webm,
                    'md5': '',
                    'size': '1080p',
                    'width': 1920
                }
            ]
        })
        self.mock_pillar('GET', '/users/56354417c379cf012919cc8b', json={
            'email': 'jpbouza@example.com',
            'full_name': 'Juan Pablo Bouza'
        })
        # Getting the children
        self.mock_pillar('GET', '/nodes', json={'_items': []})
