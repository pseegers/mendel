from unittest import TestCase
from unittest.mock import patch

from invoke import Result

from mendel.config.service_config import ServiceConfig
from mendel.deployer.remote_jar import RemoteJarDeployer
from .helpers import MockConnection


class BaseDeployerDeployTests(TestCase):
    """
    These tests test some of the business logic,
    especially with respect to integrity of individual method results.
    but most importantly they test for Fabric syntax being correct.
    """

    def setUp(self) -> None:
        super().setUp()
        mock_config = ServiceConfig()
        mock_config.slack_url = 'slack.com/aaa'
        mock_config.slack_emoji = ':alert:'
        mock_config.deployment_user = 'kevin'
        mock_config.service_name = 'test_service'
        mock_config.service_root = '/srv/'
        mock_config.graphite_host = 'int.graphite.com'
        mock_config.track_event_endpoint = 'endpoint.com'
        self.deployer = RemoteJarDeployer(config=mock_config)

    @patch('mendel.deployer.base.Deployer._track_event')
    @patch('mendel.deployer.base.Deployer._start_or_restart')
    @patch('mendel.deployer.remote_jar.RemoteJarDeployer.install')
    @patch('mendel.deployer.remote_jar.RemoteJarDeployer.upload')
    @patch('mendel.deployer.base.Deployer.build')
    def test_deploy_polymorphism(self, build, upload, install, restart, track):
        mock_connection = MockConnection(host='prod-something-01', run=Result('200'))
        result = self.deployer.deploy(mock_connection)
        self.assertTrue(build.called)
        self.assertTrue(upload.called)
        self.assertTrue(install.called)
        self.assertTrue(restart.called)
        self.assertTrue(track.called)

    @patch('mendel.deployer.base.Deployer._get_commit_hash')
    def test_new_release_dir(self, mock_commit_hash):
        mock_commit_hash.return_value = '1232435zzz'
        mock_connection = MockConnection(host='prod-something-01')
        self.deployer.project_version = '2.9.9'
        result = self.deployer._new_release_dir(mock_connection)
        self.assertTrue('kevin-1232435zzz-2.9.9' in result)

    @patch('requests.head')
    @patch('mendel.deployer.remote_jar.RemoteJarDeployer._generate_nexus_url')
    def test_already_deployed(self, nexus_url, head_req):
        nexus_url.return_value = 'http://int.my_nexus.com'
        head_req.return_value.status_code = 200
        mock_connection = MockConnection(host='prod-something-01')
        result = self.deployer.already_deployed(mock_connection)
        self.assertTrue(result)
        self.assertTrue(self.deployer.already_deployed(mock_connection))
        self.assertTrue(self.deployer._already_deployed)

    @patch('requests.head')
    @patch('mendel.deployer.remote_jar.RemoteJarDeployer._generate_nexus_url')
    def test_not_already_deployed(self, nexus_url, head_req):
        nexus_url.return_value = 'http://int.my_nexus.com'
        head_req.return_value.status_code = 404
        mock_connection = MockConnection(host='prod-something-01')
        result = self.deployer.already_deployed(mock_connection)
        self.assertFalse(result)
        self.assertFalse(self.deployer._already_deployed)
