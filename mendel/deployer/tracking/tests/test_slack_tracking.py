import json
from unittest import TestCase
from unittest.mock import patch

from mendel.deployer.tracking.slack import track_event_slack


class SlackTrackingTests(TestCase):
    def setUp(self) -> None:
        super().setUp()

    @patch('requests.post')
    def test_no_slack_url_allowed(self, mock_post):
        track_event_slack(slack_url=None, event='deployed', service_name='my_service', deployment_user='james',
                          deployment_host='aws-123', project_version='0.1.0', slack_emoji=':dabomb:')

        self.assertFalse(mock_post.called)
        # No error

    @patch('requests.post')
    def test_slack_request(self, mock_post):
        slack_url = 'ttp://slack.com/1234/adjaeifj'
        track_event_slack(slack_url=slack_url, event='deployed',
                          service_name='my_service', deployment_user='james',
                          deployment_host='aws-123', project_version='0.1.0', slack_emoji=':dabomb:',
                          commit_hash='6g7l9p')
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(mock_post.call_args[1]['url'], slack_url)
        self.assertEqual(json.loads(mock_post.call_args[1]['data'])['username'], 'Mendel 3')
        self.assertEqual(json.loads(mock_post.call_args[1]['data'])['icon_emoji'], ':dabomb:')
        self.assertEqual(json.loads(mock_post.call_args[1]['data'])['text'],
                         'james *DEPLOYED* my_service @ 6g7l9p, version *0.1.0* to host(s) aws-123')