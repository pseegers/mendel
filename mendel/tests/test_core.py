import json

from unittest import TestCase
from mock import MagicMock
from mock import patch

from mendel.core import Mendel
from fabric.state import env


class MendelCoreTest(TestCase):

    def test_tracking_does_not_break_deploy(self):
        mock_core = Mendel("some_name", slack_url="some_url")
        env.hosts = "127.0.0.1"
        mock_core.build = MagicMock()
        mock_core.upload = MagicMock()
        mock_core.install = MagicMock()
        mock_core._start_or_restart = MagicMock()
        mock_core._track_event_graphite = MagicMock()
        mock_core._track_event_api = MagicMock()
        self.assertRaises(ValueError, mock_core.deploy)
        mock_core.build.assert_called_with()
        mock_core.upload.assert_called_with()
        mock_core.install.assert_called_with()
        mock_core._start_or_restart.assert_called_with()
        mock_core._track_event_graphite.assert_called_with('deployed')
        mock_core._track_event_api.assert_called_with('deployed')

    @patch('urllib2.urlopen')
    def test_track_event_graphite(self, urlopen):
        mendel = Mendel(service_name='myservice')
        mendel._graphite_host = 'somehost'
        urlopen.return_value = MagicMock()
        urlopen.return_value.code = 200

        mendel._track_event_graphite('deployed')

        (url, payload), _ = urlopen.call_args
        json_payload = json.loads(payload)
        self.assertIsInstance(json_payload['tags'], list)
