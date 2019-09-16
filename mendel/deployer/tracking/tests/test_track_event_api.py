import json
from unittest import TestCase
from unittest.mock import patch

from mendel.deployer.tracking.api import track_event_api


class ExternalApiTrackingTests(TestCase):
    def setUp(self) -> None:
        super().setUp()

    @patch('requests.post')
    def test_no_external_api_url_allowed(self, mock_post):
        track_event_api(track_event_endpoint=None, event='deployed', service_name='my_service', deployment_user='james',
                        deployment_host='aws-123')

        self.assertFalse(mock_post.called)
        # No error

    @patch('requests.post')
    def test_api_tracking_request(self, mock_post):
        url = 'api/1234/adjaeifj'

        track_event_api(track_event_endpoint=url, event='deployed',
                        service_name='my_service', deployment_user='james',
                        deployment_host='aws-123')
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1]['url'], 'http://' + url)
        self.assertEqual(mock_post.call_args[1]['data']['service'], 'my_service')
        self.assertEqual(mock_post.call_args[1]['data']['host'], 'aws-123')
        self.assertEqual(mock_post.call_args[1]['data']['deployer'], 'james')
        self.assertEqual(mock_post.call_args[1]['data']['event'], 'deployed')
