"""
Deploy a jar
"""

from mendel.config.service_config import ServiceConfig
from mendel.util.colors import green
from .base import Deployer
from .mixins.rollback import SymlinkRollbackMixin


class JarDeployer(Deployer, SymlinkRollbackMixin):
    def __init__(self, service_name: str = None, config: ServiceConfig = None):
        super().__init__(service_name, config)
        self.release_dir = None

    def install(self, connection):
        if not self.release_dir:
            self.release_dir = self._new_release_dir(connection)
        release_path = self._rpath('releases', self.release_dir)
        connection.sudo(f'chown {self.config.user}:{self.config.group} {release_path}/{self.config.jar_name}.jar')

        self._change_symlink_to(connection, release_path=self._rpath('releases', self.release_dir))
        print(green(self.INSTALL_SUCCESS_MESSAGE % self.config.service_name))

    def upload(self, connection, bundle_name=None):
        """
        Create a new release dir and upload jar
        """
        try:
            bundle_name = self._get_bundle_name(connection)
        except Exception as e:
            self._log_error_and_exit(connection, message=str(e))

        self._create_if_missing(connection, path=self._rpath('releases'))
        self.release_dir = self._new_release_dir(connection)
        self._create_if_missing(connection, path=self._rpath('releases', self.release_dir))
        fq_jar_name = self._lpath(self.config.build_target_path, bundle_name)

        # There is no way in fabric 2 to put with sudo, workaround used https://github.com/fabric/fabric/issues/1750
        connection.put(fq_jar_name, self._tpath())
        release_target = self._rpath('releases', self.release_dir)
        connection.sudo(f'mv {self._tpath()}/{bundle_name} {release_target}')

        print(green(self.UPLOAD_SUCCESS_MESSAGE % (bundle_name, self.release_dir)))

        return self.release_dir

    def rollback(self, connection):
        """
        [core]\t\tchoose a version to rollback to from all available releases
        """
        return self.symlink_rollback(connection)

    def _get_bundle_name(self, connection):
        build_path = self._lpath(self.config.build_target_path)
        try:
            result = connection.local(f'cd {build_path} && ls {self.config.jar_name}.jar')
        except Exception:
            print(f'could not find bundle in build_target_path: {build_path}')
            raise
        if not result.ok:
            raise Exception(f'couldn\'t find bundle in {build_path}')
        bundle_file = result.stdout.strip()
        return bundle_file
