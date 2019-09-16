import json
from unittest import TestCase
from unittest.mock import patch

from mendel.deployer.tracking.graphite import track_event_graphite


class GraphiteTrackingTests(TestCase):
    def setUp(self) -> None:
        super().setUp()

    @patch('requests.post')
    def test_no_graphite_url_allowed(self, mock_post):
        track_event_graphite(graphite_host=None, event='deployed', service_name='my_service', deployment_user='james',
                             deployment_host='aws-123', project_version='0.1.0')

        self.assertFalse(mock_post.called)
        # No error

    @patch('requests.post')
    def test_graphite_request(self, mock_post):
        url = 'statsd:3001/1234/adjaeifj'
        track_event_graphite(graphite_host=url, event='deployed',
                             service_name='my_service', deployment_user='james',
                             deployment_host='aws-123', project_version='0.1.0')
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1]['url'], 'http://' + url + '/events/')
        self.assertEqual(json.loads(mock_post.call_args[1]['data'])['what'],
                         'james deployed my_service version 0.1.0 on host aws-123')
        self.assertEqual(set(json.loads(mock_post.call_args[1]['data'])['tags']), {'my_service', 'deployed'})
