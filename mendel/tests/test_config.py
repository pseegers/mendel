import os
from unittest import TestCase

from mendel.conf import Config


class TestConfigParsing(TestCase):

    def setUp(self):
        pass

    def _set_config_file(self, filename):
        root_path = os.path.dirname(os.path.abspath(__file__))
        fixture_path = os.path.join(root_path, 'fixtures')
        fq_filename = os.path.join(fixture_path, filename)
        os.environ['MENDEL_CONFIG_FILE'] = fq_filename

    def test_no_config_file(self):
        self._set_config_file('does_not_exist.conf')
        config = Config()
        self.assertEqual(config.NEXUS_USER, None)
        self.assertEqual(config.NEXUS_USER, None)
        self.assertEqual(config.NEXUS_PORT, 0)
        self.assertEqual(config.NEXUS_REPOSITORY, None)
        self.assertEqual(config.GRAPHITE_HOST, None)

    def test_nexus_config_options(self):
        self._set_config_file('nexus_configured.conf')
        config = Config()
        self.assertEqual(config.NEXUS_USER, 'username')
        self.assertEqual(config.NEXUS_HOST, 'mynexushost.int.mycompany.com')
        self.assertEqual(config.NEXUS_PORT, 8080)
        self.assertEqual(config.NEXUS_REPOSITORY, 'releases')
        self.assertEqual(config.GRAPHITE_HOST, None)

    def test_graphite_config_options(self):
        self._set_config_file('graphite_configured.conf')
        config = Config()
        self.assertEqual(config.NEXUS_USER, None)
        self.assertEqual(config.NEXUS_HOST, None)
        self.assertEqual(config.NEXUS_PORT, 0)
        self.assertEqual(config.NEXUS_REPOSITORY, None)
        self.assertEqual(config.GRAPHITE_HOST, 'graphite.int.mycompany.com')

    def test_track_event_endpoint_options(self):
        self._set_config_file('track_event_configured.conf')
        config = Config()
        self.assertEqual(config.NEXUS_USER, None)
        self.assertEqual(config.NEXUS_HOST, None)
        self.assertEqual(config.NEXUS_PORT, 0)
        self.assertEqual(config.NEXUS_REPOSITORY, None)
        self.assertEqual(config.GRAPHITE_HOST, None)
        self.assertEqual(config.TRACK_EVENT_ENDPOINT, 'api.int.mycompany.com/track/')
