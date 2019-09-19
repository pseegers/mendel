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
        mock_config = ServiceConfig(service_name='test_service',
                                    service_root='/srv/',
                                    slack_url='slack.com/aaa',
                                    slack_emoji=':alert:',
                                    deployment_user='kevin',
                                    graphite_host='int.graphite.com',
                                    track_event_endpoint='endpoint.com',
                                    build_target_path='/target/test_service')
        self.deployer = TarballDeployer(config=mock_config)

    def test_get_bundle_name(self):
        mock_connection = MockConnection(host='prod-something-01', run=Result('myservice-tgz.tar.gz'))
        result = self.deployer._get_bundle_name(mock_connection)
        self.assertEqual('myservice-tgz.tar.gz', result)
