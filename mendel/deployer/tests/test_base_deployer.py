from unittest import TestCase
from unittest.mock import patch

import pytest
from invoke import Result

from mendel.config.service_config import ServiceConfig
from mendel.deployer.base import Deployer
from .helpers import MockConnection


class BaseDeployerTests(TestCase):
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
        self.deployer = Deployer(config=mock_config)

    def test_git_commit_hash(self):
        mock_connection = MockConnection(run=Result('f333c776c8cf9d56a4604ff29640326f50f00c19'))
        result = self.deployer._get_commit_hash(mock_connection)
        self.assertEqual(result, 'f333c776c8cf9d56a4604ff29640326f50f00c19')

    def test_git_commit_hash_short(self):
        mock_connection = MockConnection(run=Result('f333c77'))
        result = self.deployer._get_commit_hash(mock_connection, shorten=True)
        self.assertEqual(result, 'f333c77')

    @patch('mendel.deployer.base.track_event_slack')
    def test_log_and_exit(self, slack):
        with pytest.raises(SystemExit) as e:
            mock_connection = MockConnection(host='prod-something-01')
            result = self.deployer._log_error_and_exit(mock_connection, 'something went wrong')
            self.assertTrue('something went wrong' in result.stdout)
            self.assertTrue(slack.called)

    @patch('mendel.deployer.base.track_event_api')
    @patch('mendel.deployer.base.track_event_graphite')
    @patch('mendel.deployer.base.track_event_slack')
    @patch('mendel.deployer.base.Deployer._get_commit_hash')
    def test_track_event(self, commit_hash, slack, graphite, api):
        commit_hash.return_value = '123aaa'
        mock_connection = MockConnection(host='prod-something-01')
        result = self.deployer._track_event(mock_connection, 'deployed')
        self.assertTrue(slack.called)
        self.assertTrue(graphite.called)
        self.assertTrue(api.called)

    def test_get_current_release(self):
        release = '/srv/my-service/releases/20190809-184022-user-be07d4d1fa4b0-2.9.9'
        mock_connection = MockConnection(host='prod-something-01', sudo=Result(release))
        result = self.deployer._get_current_release(mock_connection)
        self.assertEqual(result, '20190809-184022-user-be07d4d1fa4b0-2.9.9')

    @patch('mendel.deployer.base.Deployer._get_commit_hash')
    def test_new_release_dir(self, mock_commit_hash):
        mock_commit_hash.return_value = '1232435zzz'
        mock_connection = MockConnection(host='prod-something-01')
        result = self.deployer._new_release_dir(mock_connection)
        self.assertTrue('kevin-1232435zzz' in result)

    def test_change_symlink_to(self):
        mock_connection = MockConnection(host='prod-something-01', sudo=Result())
        result = self.deployer._change_symlink_to(mock_connection, '/srv/blah/my-new-release')

    def test_get_lastest_release(self):
        output = """
            drwxr-xr-x 2 test-service test-service     4096 Jun 21 15:40 20190621-154051-user1-a2cf33a262e5ea-1.1.10
            drwxr-xr-x 2 test-service test-service     4096 May 14 14:14 20190514-141448-user2-64e068d9bad243a1-1.1.9
            drwxr-xr-x 2 test-service test-service     4096 Mar 22 14:02 20190322-140208-user2-ada793358096e561-1.1.8
        """
        mock_connection = MockConnection(host='prod-something-01', run=Result(output))
        result = self.deployer._get_latest_release(mock_connection)
        self.assertEqual(result, '20190621-154051-user1-a2cf33a262e5ea-1.1.10')

    @patch('mendel.deployer.base.exists')
    def test_create_if_missing(self, patchwork_exists):
        patchwork_exists.return_value = False
        mock_connection = MockConnection(host='prod-something-01', sudo=Result())
        result = self.deployer._create_if_missing(mock_connection, '/srv/blah/my-new-release')

    @patch('mendel.deployer.base.Deployer._get_latest_release')
    def test_link_latest_release(self, latest_release_mock):
        latest_release_mock.return_value = '2019-01-kevin-1209876757'
        mock_connection = MockConnection(host='prod-something-01', sudo=Result())
        result = self.deployer.link_latest_release(mock_connection)

    @patch('mendel.deployer.base.Deployer.service_wrapper')
    def test_is_running_true(self, service_wrapper):
        status = """
           Loaded: loaded (/etc/systemd/system/test-service.service; enable
           Active: active (running) since Thu 2019-08-29 10:46:01 UTC; 15h ago
           Main PID: 1335 (openjdk8)
        """
        service_wrapper.return_value = status
        mock_connection = MockConnection(host='prod-something-01')
        result = self.deployer._is_running(mock_connection)
        self.assertTrue(result)

    @patch('mendel.deployer.base.Deployer.service_wrapper')
    def test__is_running_false(self, service_wrapper):
        status = """
           Loaded: loaded (/etc/systemd/system/test-service.service; enable
           Active: inactive (dead) since Fri 2019-08-30 01:58:05 UTC; 1s ago
           Process: 1335 ExecStart=/usr/local/bin/openjdk8 -Xmx1024M -Dlog4j.configurat
           Main PID: 1335 (code=exited, status=0/SUCCESS)
        """
        service_wrapper.return_value = status
        mock_connection = MockConnection(host='prod-something-01')
        result = self.deployer._is_running(mock_connection)
        self.assertFalse(result)

    def test_service_wrapper_not_whitelisted(self):
        mock_connection = MockConnection(host='prod-something-01')
        with pytest.raises(SystemExit) as e:
            result = self.deployer.service_wrapper(mock_connection, 'delete')

    def test_service_wrapper_start(self):
        mock_connection = MockConnection(host='prod-something-01', run=[Result(), Result()])
        result = self.deployer.service_wrapper(mock_connection, 'start')

    def test_service_ubuntu_18_start(self):
        mock_connection = MockConnection(host='prod-something-01', run=[Result('Release:        18.04'), Result()])
        result = self.deployer.service_wrapper(mock_connection, 'start')


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
        self.deployer = Deployer(config=mock_config)

    @patch('mendel.deployer.base.Deployer._track_event')
    @patch('mendel.deployer.base.Deployer._start_or_restart')
    @patch('mendel.deployer.base.Deployer.install')
    @patch('mendel.deployer.base.Deployer.upload')
    @patch('mendel.deployer.base.Deployer.build')
    def test_deploy_tracking_ok(self, build, upload, install, restart, track):
        mock_connection = MockConnection(host='prod-something-01', run=Result('200'))
        result = self.deployer.deploy(mock_connection)
        self.assertTrue(build.called)
        self.assertTrue(upload.called)
        self.assertTrue(install.called)
        self.assertTrue(restart.called)
        self.assertTrue(track.called)

    @patch('mendel.deployer.base.Deployer._track_event')
    @patch('mendel.deployer.base.Deployer._start_or_restart')
    @patch('mendel.deployer.base.Deployer.install')
    @patch('mendel.deployer.base.Deployer.upload')
    @patch('mendel.deployer.base.Deployer.build')
    def test_deploy_tracking_broken(self, build, upload, install, restart, track):
        mock_connection = MockConnection(host='prod-something-01', run=Result('400'))
        with pytest.raises(SystemExit) as e:
            result = self.deployer.deploy(mock_connection)
            self.assertFalse(build.called)
            self.assertFalse(upload.called)
            self.assertFalse(install.called)
            self.assertFalse(restart.called)
            self.assertFalse(track.called)