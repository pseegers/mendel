"""
Deploy a jar housed remotely (Nexus)
"""
import datetime

import requests

from mendel.config.service_config import ServiceConfig
from mendel.util.colors import blue
from mendel.util.colors import green
from .base import Deployer
from .mixins.nexus import NexusMixin
from .mixins.rollback import SymlinkRollbackMixin


class RemoteJarDeployer(Deployer, NexusMixin, SymlinkRollbackMixin):
    def __init__(self, service_name: str = None, config: ServiceConfig = None):
        super().__init__(service_name, config)
        self._already_deployed = False

    def install(self, connection):
        """
        [advanced]\t Install jar on the remote host
        :param connection: Connection
        :return: Nothing
        """
        nexus_url = self._generate_nexus_url(connection)
        self._create_if_missing(connection, path=self._rpath('releases'))
        release_dir = self._new_release_dir(connection)
        self._create_if_missing(connection, path=self._rpath('releases', release_dir))

        current_release = self._rpath('releases', release_dir)
        connection.sudo(f'wget {nexus_url} --directory-prefix={current_release}', hide=True)
        # rename versioned jar to normal service jar
        connection.sudo(f'mv {current_release}/*.jar {current_release}/{self.config.jar_name}.jar')
        connection.sudo(f'chown {self.config.user}:{self.config.group} {current_release}/{self.config.jar_name}.jar')

        self._change_symlink_to(connection=connection, release_path=self._rpath('releases', release_dir))
        print(green(self.INSTALL_SUCCESS_MESSAGE % self.config.service_name))

    def upload(self, connection):
        """
        [advanced]\t Deploy jar to nexus if not already present
        :param connection: Connection
        :return:
        """
        if not self.already_deployed(connection):
            if self.config.project_type == "java":
                print(blue('Pushing jar to nexus server'))
                connection.local('mvn deploy')
                self._already_deployed = True
            else:
                raise Exception(f"Unsupported project type: {self.config.project_type}")

    def already_built(self, connection):
        return self.already_deployed(connection)

    def already_deployed(self, connection):
        """
        Check if jar has already been deployed to the central repository (nexus)
        Check first time, and caches it on an instance variable thereafter.
        :param connection: Connection
        :return: bool whether jar is already deployed
        """
        if self._already_deployed:
            return True
        else:
            nexus_url = self._generate_nexus_url(connection)
            resp = requests.head(url=nexus_url, timeout=3)

            if resp.status_code == 200:
                print(green('Already found artifact in nexus. Skipping build and upload phases...'))
                self._already_deployed = True
                return True
            else:
                print(print(resp.content))
                blue('Artifact not found in nexus. Building locally...')
        return False

    def rollback(self, connection):
        """
        Redirect to mixin.
        """
        return self.symlink_rollback(connection)

    def _new_release_dir(self, connection):
        """
        Generate a new release dir for the remote hosts, this needs to be the same across hosts
        Note this is overridden from the base class - this variant includes project version
        in addition to the commit hash, user and timestamp on the base class.
        :param connection: Connection
        :return: str release dir
        """
        release_dir_timestamp = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        commit_hash = self._get_commit_hash(connection)

        release_dir = f'{release_dir_timestamp}-{self.config.deployment_user}-{commit_hash}-{self.project_version}'
        print(blue(f"Release directory set to {release_dir}"))

        return release_dir
