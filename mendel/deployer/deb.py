"""
Deploy a debian package
"""
from patchwork.files import exists

from mendel.config.service_config import ServiceConfig
from mendel.util.colors import green
from .base import Deployer
from .mixins.rollback import SymlinkRollbackMixin


class DebDeployer(Deployer):
    def __init__(self, service_name, config):
        super().__init__(service_name, config)

    def upload(self, connection):
        """
        upload a deb to /tmp,  return path
        """
        try:
            bundle_name = self._get_bundle_name(connection)
        except Exception as e:
            self._log_error_and_exit(connection, message=str(e))

        dest = self._tpath()
        fq_bundle_file = self._lpath(self.config.build_target_path, bundle_name)
        connection.put(fq_bundle_file, dest)

        print(green(self.UPLOAD_SUCCESS_MESSAGE % (bundle_name, dest)))

        return dest

    def install(self, connection):
        """
        Install debian package on remote host
        :param connection: Connection
        :return: nothing
        """
        try:
            bundle_name = self._get_bundle_name(connection)
        except Exception as e:
            self._log_error_and_exit(connection, message=str(e))

        self._backup_current_release(connection)
        fq_bundle_file = self._tpath(bundle_name)
        connection.sudo(f'dpkg --force-confold -i {fq_bundle_file}', hide='stdout')
        self.link_latest_release(connection)
        print(green(self.INSTALL_SUCCESS_MESSAGE % self.config.service_name))

    def _get_bundle_name(self, connection):
        build_path = self._lpath(self.config.build_target_path)
        try:
            result = connection.local(f'cd {build_path} && ls *.deb')
        except Exception:
            print(f'could not find bundle in build_target_path: {build_path}')
            raise
        if not result.ok:
            raise Exception(f'couldn\'t find bundle in {build_path}')
        bundle_file = result.stdout.strip()
        return bundle_file

    def _backup_current_release(self, connection):
        """

        [advanced]\t

        dpkg likes to blow away your old files when
        you make new ones. this is a hack to keep them
        around
        """
        current_release = self._rpath('releases', self._get_current_release(connection)).rstrip('/')

        should_backup = '.old' not in current_release and \
            not exists(connection, current_release + '.old')

        if should_backup:
            connection.sudo('mv %(dir)s %(dir)s.old' % {'dir': current_release})
            self._change_symlink_to(connection, release_path="%s.old" % current_release)
