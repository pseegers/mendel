"""
Deploy a tarball
"""
from mendel.config.service_config import ServiceConfig
from mendel.util.colors import green
from .base import Deployer
from .mixins.rollback import SymlinkRollbackMixin


class TarballDeployer(Deployer, SymlinkRollbackMixin):
    def __init__(self, service_name: str = None, config: ServiceConfig = None):
        super().__init__(service_name, config)
        self.release_dir = None

    def install(self, connection):
        try:
            bundle_name = self._get_bundle_name(connection)
        except Exception as e:
            self._log_error_and_exit(connection, message=str(e))

        if not self.release_dir:
            self.release_dir = self._new_release_dir(connection)
        release_destination = self._rpath('releases', self.release_dir)
        connection.run(
            f'cd {release_destination} && sudo tar --strip-components 1 -zxvf {bundle_name} && sudo rm {bundle_name}')

        if self.config.project_type == 'java':
            connection.run(f'cd {release_destination} && sudo ln -sf *.jar {self.config.service_name}.jar')
            self._change_symlink_to(connection, self._rpath('releases', self.release_dir))

        elif self.config.project_type == 'python':
            # fabric commands are each issued in their own shell so the virtual env needs to be activated each time
            # pip had issues with wheel cache permissions which were solved with the --no-cache flag
            # the requires.txt is used instead of setup.py install because we don't need the code installed as a module
            #   but we still need to the requirements installed, this way we dont have to find a requirements.txt file
            #   in the rest of the application b/c setup.py sdist puts it in the egg-info
            connection.sudo(
                f'source /srv/{self.config.service_name}/env/bin/activate && pip install --no-cache -r {release_destination}/{self.config.service_name}.egg-info/requires.txt')
            # need to get the top level application directory but not the egg-info directory or other setup files
            project_dir = connection.sudo("find . -maxdepth 1 -mindepth 1 -type d -not -regex '.*egg-info$'")
            project_dir = project_dir[2:]  # find command returns a string like './dir'
            self._change_symlink_to(connection, release_path=self._rpath('releases', self.release_dir, project_dir))

        print(green(self.INSTALL_SUCCESS_MESSAGE % self.config.service_name))

    def upload(self, connection, bundle_name=None):
        """
        create a new release dir and upload tarball
        """
        try:
            bundle_name = self._get_bundle_name(connection)
        except Exception as e:
            self._log_error_and_exit(connection, message=str(e))

        self._create_if_missing(connection, self._rpath('releases'))
        self.release_dir = self._new_release_dir(connection)
        self._create_if_missing(connection, self._rpath('releases', self.release_dir))
        fq_bundle_file = self._lpath(self.config.build_target_path, bundle_name)
        # There is no way in fabric 2 to put with sudo, workaround used https://github.com/fabric/fabric/issues/1750
        connection.put(fq_bundle_file, self._tpath())
        release_target = self._rpath('releases', self.release_dir)
        connection.sudo(f'mv {self._tpath()}/{bundle_name} {release_target}')

        print(green(self.UPLOAD_SUCCESS_MESSAGE % (bundle_name, self.release_dir)))

        return self.release_dir

    def _get_bundle_name(self, connection):
        build_path = self._lpath(self.config.build_target_path)
        try:
            result = connection.local(f'cd {build_path} && ls -1t *.tar.gz | head -1', hide=True)
        except Exception:
            print('could not find bundle in build_target_path:', self._lpath(self.config.build_target_path))
            raise
        if not result.ok:
            raise Exception(f'couldn\'t find bundle in {build_path}')

        bundle_file = result.stdout.strip()
        return bundle_file
