import json

from unittest import TestCase
from mock import MagicMock
from mock import patch

from mendel.core import Mendel
from fabric.state import env


class MendelCoreTest(TestCase):

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
