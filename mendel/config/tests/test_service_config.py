import os
from test.support import EnvironmentVarGuard
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from mendel.config.service_config import ServiceConfig
from mendel.config.service_config import load_mendel_config


@patch('argparse.ArgumentParser.parse_known_args')
class ServiceConfigTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.env = EnvironmentVarGuard()
        self.root_path = os.path.dirname(os.path.abspath(__file__))
        self.fixture_path = os.path.join(self.root_path, 'fixtures')

    def _set_global_config_file(self, filename):
        config_filename = os.path.join(self.fixture_path, filename)
        self.env.set('MENDEL_CONFIG_FILE', config_filename)

    def test_remote_jar_happy_path(self, arg_parser):
        global_config_name = 'sample_mendel_conf.conf'
        mendelfile_name = 'remote_jar_mendelfile.yml'
        mendelfile = os.path.join(self.fixture_path, mendelfile_name)
        options_mock = MagicMock(file=mendelfile)
        arg_parser.return_value = options_mock, MagicMock()
        with self.env:
            self._set_global_config_file(global_config_name)
            config, _ = load_mendel_config()
            self.assertEqual(config.service_name, 'hello-world')
            self.assertEqual(config.service_root, '/srv/hello-world')
            self.assertEqual(config.build_target_path, 'target/hello-world')
            self.assertEqual(config.user, 'hello-world')
            self.assertEqual(config.group, 'hello-world')
            self.assertEqual(config.bundle_type, 'remote_jar')
            self.assertEqual(config.project_type, 'java')
            self.assertEqual(config.cwd, ServiceConfig.DEFAULT_CWD)
            self.assertEqual(config.jar_name, 'hello-world')
            self.assertEqual(config.classifier, None)
            self.assertEqual(config.nexus_user, config.GLOBAL_NEXUS_USER)
            self.assertEqual(config.nexus_host, config.GLOBAL_NEXUS_HOST)
            self.assertEqual(config.nexus_port, config.GLOBAL_NEXUS_PORT)
            self.assertEqual(config.nexus_repository, config.GLOBAL_NEXUS_REPOSITORY)
            self.assertEqual(config.graphite_host, config.GLOBAL_GRAPHITE_HOST)
            self.assertEqual(config.api_service_name, 'hello-world')
            self.assertEqual(config.slack_url, 'https://hooks.slack.com/services/a/b/c')
            self.assertEqual(config.slack_emoji, ServiceConfig.DEFAULT_SLACK_EMOJI)
            self.assertEqual(config.use_upstart, True)
            self.assertEqual(config.use_init, False)

    def test_host_configuration(self, arg_parser):
        global_config_name = 'sample_mendel_conf.conf'
        mendelfile_name = 'remote_jar_mendelfile.yml'
        mendelfile = os.path.join(self.fixture_path, mendelfile_name)
        options_mock = MagicMock(file=mendelfile)
        arg_parser.return_value = options_mock, MagicMock()
        with self.env:
            self._set_global_config_file(global_config_name)
            config, _ = load_mendel_config()
            host_configs = config.host_configs
            self.assertEqual(len(host_configs), 2)
            self.assertEqual(host_configs[0].name, 'prod')
            self.assertEqual(host_configs[0].port, 22)
            self.assertEqual(set(host_configs[0].hosts), {'aws-1-3-4', 'aws-1-3-5'})
            self.assertEqual(host_configs[1].name, 'stage')
            self.assertEqual(host_configs[1].port, 22)
            self.assertEqual(set(host_configs[1].hosts), {'dev-123'})
            self.assertEqual(set(config.available_host_groups.keys()), {'stage', 'prod'})
