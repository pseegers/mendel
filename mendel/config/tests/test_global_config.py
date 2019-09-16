import os

from unittest import TestCase
from test.support import EnvironmentVarGuard

from mendel.config.global_config import GlobalConfig


class GlobalConfigTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.env = EnvironmentVarGuard()

    def _set_config_file(self, filename):
        root_path = os.path.dirname(os.path.abspath(__file__))
        fixture_path = os.path.join(root_path, 'fixtures')
        fq_filename = os.path.join(fixture_path, filename)
        self.env.set('MENDEL_CONFIG_FILE', fq_filename)

    def test_happy_path(self):
        with self.env:
            self._set_config_file('sample_mendel_conf.conf')
            config = GlobalConfig()
            self.assertEqual(config.GLOBAL_NEXUS_USER, 'ops-deployer')
            self.assertEqual(config.GLOBAL_NEXUS_HOST, 'nexus.mycompany.com')
            self.assertEqual(config.GLOBAL_NEXUS_PORT, 8081)
            self.assertEqual(config.GLOBAL_NEXUS_REPOSITORY, 'http://nexus.mycompany.com:8081/nexus/a/reps/rel/')
            self.assertEqual(config.GLOBAL_GRAPHITE_HOST, 'carbon-mycompany.com')

    def test_no_config_file(self):
        with self.env:
            self._set_config_file('does_not_exist.conf')
            config = GlobalConfig()
            self.assertEqual(config.GLOBAL_NEXUS_USER, None)
            self.assertEqual(config.GLOBAL_NEXUS_HOST, None)
            self.assertEqual(config.GLOBAL_NEXUS_PORT, 0)
            self.assertEqual(config.GLOBAL_NEXUS_REPOSITORY, None)
            self.assertEqual(config.GLOBAL_GRAPHITE_HOST, None)

    def test_nexus_config_options(self):
        with self.env:
            self._set_config_file('nexus_configured.conf')
            config = GlobalConfig()
            self.assertEqual(config.GLOBAL_NEXUS_USER, 'username')
            self.assertEqual(config.GLOBAL_NEXUS_HOST, 'mynexushost.int.mycompany.com')
            self.assertEqual(config.GLOBAL_NEXUS_PORT, 8080)
            self.assertEqual(config.GLOBAL_NEXUS_REPOSITORY, 'releases')
            self.assertEqual(config.GLOBAL_GRAPHITE_HOST, None)

    def test_graphite_config_options(self):
        with self.env:
            self._set_config_file('graphite_configured.conf')
            config = GlobalConfig()
            self.assertEqual(config.GLOBAL_NEXUS_USER, None)
            self.assertEqual(config.GLOBAL_NEXUS_HOST, None)
            self.assertEqual(config.GLOBAL_NEXUS_PORT, 0)
            self.assertEqual(config.GLOBAL_NEXUS_REPOSITORY, None)
            self.assertEqual(config.GLOBAL_GRAPHITE_HOST, 'graphite.int.mycompany.com')

    def test_track_event_endpoint_options(self):
        with self.env:
            self._set_config_file('track_event_configured.conf')
            config = GlobalConfig()
            self.assertEqual(config.GLOBAL_NEXUS_USER, None)
            self.assertEqual(config.GLOBAL_NEXUS_HOST, None)
            self.assertEqual(config.GLOBAL_NEXUS_PORT, 0)
            self.assertEqual(config.GLOBAL_NEXUS_REPOSITORY, None)
            self.assertEqual(config.GLOBAL_GRAPHITE_HOST, None)
            self.assertEqual(config.GLOBAL_TRACK_EVENT_ENDPOINT, 'api.int.mycompany.com/track/')
