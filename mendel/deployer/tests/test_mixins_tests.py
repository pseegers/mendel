import os
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch
from xml.etree.ElementTree import ElementTree

from invoke import Result

from mendel.config.service_config import ServiceConfig
from mendel.deployer.mixins.nexus import NexusMixin
from mendel.deployer.remote_jar import RemoteJarDeployer
from .helpers import MockConnection


class NexusMixinTests(TestCase):
    def setUp(self):
        super().setUp()

    @patch.object(ElementTree, 'findtext')
    def test_generate_base_nexus_url(self, mock_pom_find):
        mock_pom_find.return_value = 'com.mycompany.mydivision'
        mock_config = MagicMock(nexus_repository='http://nexus.mycompany.com:8081/nexus/a/reps/rel/',
                                jar_name='best-jar-ever',
                                classifier=None)
        nexus_mixin = NexusMixin()
        nexus_mixin.config = mock_config
        nexus_mixin.project_version = None
        self.assertEqual(nexus_mixin._generate_base_nexus_url(ElementTree()),
                         'http://nexus.mycompany.com:8081/nexus/a/reps/rel/com/mycompany/mydivision/best-jar-ever')

    @patch.object(ElementTree, 'findtext')
    @patch('mendel.deployer.mixins.nexus.ElementTree')
    def test_generate_nexus_url(self, mock_tree, mock_pom_find):
        mock_tree.return_value.findtext = mock_pom_find
        mock_pom_find.side_effect = ['1.20.0', 'com.mycompany.mydivision']
        mock_config = MagicMock(nexus_repository='http://nexus.mycompany.com:8081/nexus/a/reps/rel/',
                                jar_name='best-jar-ever',
                                classifier=None,
                                cwd='.')
        nexus_mixin = NexusMixin()
        nexus_mixin.config = mock_config
        nexus_mixin.project_version = None
        self.assertEqual(nexus_mixin._generate_nexus_url(MagicMock()),
                         'http://nexus.mycompany.com:8081/nexus/a/reps/rel/com/mycompany/mydivision/best-jar-ever/1.20.0/best-jar-ever-1.20.0.jar')

    @patch('mendel.deployer.mixins.nexus.ElementTree')
    @patch('mendel.deployer.mixins.nexus.NexusMixin._generate_base_nexus_url')
    def test_find_latest_nexus_version(self, mock_nexus_url, mock_tree):
        root_path = os.path.dirname(os.path.abspath(__file__))
        mock_nexus_url.return_value = 'nexus.com'
        fixture_path = os.path.join(root_path, 'fixtures')
        meta_file = os.path.join(fixture_path, 'maven_metadata.xml')
        with open(meta_file, 'r') as f:
            meta = f.read()
        mock_connection = MockConnection(run=Result(meta))
        mock_config = MagicMock(nexus_repository='http://nexus.mycompany.com:8081/nexus/a/reps/rel/',
                                jar_name='best-jar-ever',
                                classifier=None,
                                cwd='.')
        nexus_mixin = NexusMixin()
        nexus_mixin.config = mock_config
        res = nexus_mixin._find_latest_nexus_version(mock_connection)
        self.assertEqual(res, '2.7.0')


class SymlinkRollbackMixinTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        mock_config = ServiceConfig()
        mock_config.deployment_user = 'kevin'
        mock_config.service_name = 'test_service'
        mock_config.service_root = '/srv/'
        self.deployer = RemoteJarDeployer(config=mock_config)

    def test_get_all_releases(self):
        releases = """
            20190318-205238-user1-2c3487a97428aebf17c-1.1.6
            20190320-181250-user2-24e98fff34f5f29f7ba9e-1.1.7
            20190322-134809-user1-ada79335c2fa4ed8096e561-1.1.8
            20190322-135852-maxjohnson-ada79335c2a4ed8096e561-1.1.8
        """
        mock_connection = MockConnection(host='prod-something-01', sudo=Result(releases))
        result = self.deployer._get_all_releases(mock_connection)
        self.assertEqual(result[0], '20190318-205238-user1-2c3487a97428aebf17c-1.1.6')
        self.assertEqual(result[1], '20190320-181250-user2-24e98fff34f5f29f7ba9e-1.1.7')

    def test_display_releases_for_rollback_selection(self):
        releases = ['20190318-205238-user1-2c3487a97428aebf17c-1.1.6',
                    '20190320-181250-user2-24e98fff34f5f29f7ba9e-1.1.7',
                    '20190322-134809-user1-ada79335c2fa4ed8096e561-1.1.8',
                    '20190809-184022-user-be07d4d1fa4b0-2.9.9']

        current = "20190809-184022-user-be07d4d1fa4b0-2.9.9"
        result = self.deployer._display_releases_for_rollback_selection(releases, current)
        self.assertEqual(result, 3)
