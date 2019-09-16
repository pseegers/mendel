from unittest import TestCase

from mendel.config.service_config import ServiceConfig
from mendel.core import Mendel
from mendel.deployer.deb import DebDeployer
from mendel.deployer.jar import JarDeployer
from mendel.deployer.remote_deb import RemoteDebDeployer
from mendel.deployer.remote_jar import RemoteJarDeployer


class MendelCoreTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.expected_tasks = {'link_latest_release', 'build', 'upload',
                               'install', 'deploy', 'rollback', 'tail', 'service_wrapper'}
        self.mock_config = ServiceConfig()
        self.mock_config.slack_url = 'slack.com/aaa'
        self.mock_config.slack_emoji = ':alert:'
        self.mock_config.deployment_user = 'kevin'
        self.mock_config.service_name = 'test_service'

    def test_remote_jar_tasks(self):
        self.mock_config.bundle_type = 'remote_jar'
        mendel = Mendel(config=self.mock_config, hosts='my-server-01')
        self.assertTrue(isinstance(mendel.deployer, RemoteJarDeployer))
        self.assertEqual(len(mendel.tasks), 8)
        self.assertEqual({t.__name__ for t in mendel.tasks}, self.expected_tasks)

    def test_remote_deb_tasks(self):
        self.mock_config.bundle_type = 'remote_deb'
        mendel = Mendel(config=self.mock_config, hosts='my-server-01')
        self.assertTrue(isinstance(mendel.deployer, RemoteDebDeployer))
        self.assertEqual(len(mendel.tasks), 8)
        self.assertEqual({t.__name__ for t in mendel.tasks}, self.expected_tasks)

    def test_deb_tasks(self):
        self.mock_config.bundle_type = 'deb'
        mendel = Mendel(config=self.mock_config, hosts='my-server-01')
        self.assertTrue(isinstance(mendel.deployer, DebDeployer))
        self.assertEqual(len(mendel.tasks), 8)
        self.assertEqual({t.__name__ for t in mendel.tasks}, self.expected_tasks)

    def test_jar_tasks(self):
        self.mock_config.bundle_type = 'jar'
        mendel = Mendel(config=self.mock_config, hosts='my-server-01')
        self.assertTrue(isinstance(mendel.deployer, JarDeployer))
        self.assertEqual(len(mendel.tasks), 8)
        self.assertEqual({t.__name__ for t in mendel.tasks}, self.expected_tasks)