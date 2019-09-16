from unittest import TestCase
from unittest.mock import patch

from invoke import Result

from mendel.config.service_config import ServiceConfig
from mendel.deployer.tgz import TarballDeployer
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
        mock_config.build_target_path = '/target/test_service'
        self.deployer = TarballDeployer(config=mock_config)

    def test_get_bundle_name(self):
        mock_connection = MockConnection(host='prod-something-01', run=Result('myservice-tgz.tar.gz'))
        result = self.deployer._get_bundle_name(mock_connection)
        self.assertEqual('myservice-tgz.tar.gz', result)
