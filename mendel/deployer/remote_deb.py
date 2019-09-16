"""
Deploy a debian package housed remotely (Nexus)
"""
import getpass
import os

import requests
from debian import deb822
from fabric.connection import Connection

from mendel.util.colors import blue
from mendel.util.colors import green
from .base import Deployer
from .mixins.nexus import NexusMixin


class RemoteDebDeployer(Deployer, NexusMixin):

    def __init__(self, service_name, config):
        super().__init__(service_name, config)

    def install(self, connection):
        self._apt_install_latest(connection)
        print(green(self.INSTALL_SUCCESS_MESSAGE % self.config.service_name))

    def build(self, connection):
        # we "build" during the "upload" task via `mvn deploy`
        self._already_built = True
        pass

    def upload(self, connection):
        """
        upload a deb to nexus
        """
        if self.config.project_type == "java":
            connection.local('mvn clean -U deploy')
        else:
            raise Exception(f"Unsupported project type for remote deb: {self.config.project_type}")

    def rollback(self, connection):
        def validator(rollback_candidate):
            if rollback_candidate not in [v.get('Version') for v in available_versions]:
                raise Exception(f'invalid rollback selection: {rollback_candidate}')
            return rollback_candidate

        available_versions = self._get_available_nexus_versions()
        current_version = self._get_current_package_version(connection)

        curr_index = self._display_apt_versions_for_rollback_selection(
            available_versions,
            current_version
        )

        default_rollback_choice = available_versions[max(curr_index - 1, 0)].get('Version')

        rollback_to = input('Rollback to:')
        try:
            validator(rollback_to)
        except Exception as e:
            self._log_error_and_exit(connection, str(e))

        self._apt_install(connection=connection, version=rollback_to)
        self._track_event(connection, event='rolledback')

    def _get_current_package_version(self, connection: Connection):
        package_info = connection.run(f'dpkg-query -s {self.config.service_name}', hide='both')
        pkg = deb822.Packages(package_info)
        return pkg.get('Version')

    def _display_apt_versions_for_rollback_selection(self, releases, current):
        """
        displays releases with current release flagged, also returns index of
        current release in release list
        """
        r_list, curr_index = [], None
        for i, r in enumerate(releases):
            release_string = ('%s %s' % (r.get('Version'), r.get('Filename', '').split('/')[-1]))
            if current == r.get('Version'):
                r_list.append(release_string + green(' <-- current'))
                curr_index = i
            else:
                r_list.append(release_string)

        for r in r_list:
            print(r)

        return curr_index

    def _apt_install_latest(self, connection: Connection):
        print(blue(f'upgrading package {self.config.service_name} to latest available version'))
        connection.sudo('apt-get update', hide="stdout")
        connection.sudo(
            f'apt-get install -y --force-yes --only-upgrade -o Dpkg::Options::="--force-confold" {self.config.service_name}')

    def _apt_install(self, connection: Connection, version=None):
        if not version:
            self._apt_install_latest(connection)
        else:
            print(blue(f'installing {self.config.service_name} {version}'))
            connection.sudo('apt-get update', hide="stdout")
            connection.sudo(
                f'apt-get install -y --force-yes -o Dpkg::Options::="--force-confold" {self.config.service_name}={version}')

        path = self._rpath("current", self.config.service_name)
        jar_name = connection.run(f'readlink {path}.jar', hide='both')
        print(green(f'apt installed new jar: {jar_name}'))

    def _get_available_nexus_versions(self):
        # validate nexus settings are configured first
        for suffix in ('host', 'port', 'user', 'repository'):
            if not getattr(self, '_nexus_%s' % suffix):
                self._log_error_and_exit('~/.mendel.conf is missing %s in [nexus] configuration section' % suffix)

        url_for_debug = f'http://{self.config.nexus_host}:{self.config.nexus_port}' + \
                        f'/nexus/content/repositories' + \
                        f'/{self.config.nexus_repository}' + \
                        f'/Packages'

        print(blue(f'Downloading packages from {url_for_debug}'))

        # TODO maybe read password from maven settings?
        nexus_password = os.environ.get('MENDEL_NEXUS_PASSWORD') or \
            getpass.getpass(prompt='Enter nexus password: ')

        packages_file = requests.get(
            'http://%(nexus_user)s:%(nexus_password)s'
            '@%(nexus_host)s:%(nexus_port)s'
            '/nexus/content/repositories'
            '/%(nexus_repository)s'
            '/Packages' % dict(nexus_user=self.config.nexus_user,
                               nexus_password=nexus_password,
                               nexus_host=self.config.nexus_host,
                               nexus_port=self.config.nexus_port,
                               nexus_repository=self.config.nexus_repository
                               )
        ).content

        package_entries = [
            deb822.Packages(package_info)
            for package_info in packages_file.split('\n\n')
            if package_info
        ]

        available_versions = [
            p for p in package_entries if p.get('Package') == self.config.service_name
        ]

        print(blue(f'Found {len(package_entries)} available versions of {self.config.service_name}'))

        return available_versions
