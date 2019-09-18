import datetime
import os
import sys

from patchwork.files import exists

from mendel.config.service_config import ServiceConfig
from mendel.deployer.tracking.api import track_event_api
from mendel.deployer.tracking.graphite import track_event_graphite
from mendel.deployer.tracking.slack import track_event_slack
from mendel.util.colors import blue
from mendel.util.colors import green
from mendel.util.colors import magenta
from mendel.util.colors import red


class Deployer(object):
    INSTALL_SUCCESS_MESSAGE = "Successfully installed new release of %s service"
    UPLOAD_SUCCESS_MESSAGE = "Uploaded new release of %s to %s"

    def __init__(self, service_name: str = None, config: ServiceConfig = None):
        assert service_name or getattr(config, 'service_name')
        self.config = config
        self._already_built = False
        self.project_version = None

    def already_built(self, connection):
        # so we dont build multiple times for each host we're deploying to.
        return self._already_built

    # Common deployment path
    def deploy(self, connection, version=None):
        """
        [core]\t\tbuilds, installs, and deploys to all the specified hosts
        """
        # this is checked upstream when mendel is initialized. But, sanity check again
        if not connection.host:
            self._log_error_and_exit(connection,
                                     message="error: you didnt specify any hosts with -H or configuration file")

        if version and version.strip():
            self.project_version = version.strip()
            print("Version was set to be %s." % self.project_version)

        result = connection.local('curl -s -o /dev/null -w "%{http_code}" ' + str(self.config.graphite_host),
                                  hide='stdout')
        curl_output = result.stdout

        if curl_output.strip() == '200':
            print(green('Graphite host is present in mendel configuration and responsive'))
            print(blue('Proceeding with deployment...'))
        else:
            self._log_error_and_exit(connection,
                                     message='Graphite host is not present in mendel configuration or is not responsive')

        self.build(connection)
        self.upload(connection)  # Polymorphic, done in subclasses
        self.install(connection)  # Polymorphic, done in subclasses
        self._start_or_restart(connection)
        self._track_event(connection, event='deployed')

    def build(self, connection):
        """
        [advanced]\tbuilds new application bundle for your service using maven (if java)
        or setup.py (if python).

        if using java, it is highly recommended that you use the
        maven-assembly-plugin as a standard, it makes bundling files together into
        archives straightforward.

        Note: only builds once, no matter how many hosts!
        """
        if not self.already_built(connection):
            if self.project_version:
                raise Exception(
                    f"User required version {self.project_version} to be deployed, but it wasn't avaliable from remote source")
            if self.config.project_type == "java":
                connection.local('mvn clean -U package')
            elif self.config.project_type == "python":
                if self.config.bundle_type == "tgz":
                    connection.local('python setup.py sdist')
                else:
                    raise Exception(
                        f"Unsupported bundle type: {self.config.bundle_type} for project type: {self.config.project_type}")
            else:
                raise Exception(f"Unsupported project type: {self.config.project_type}")
            self._already_built = True
            track_event_slack(slack_url=self.config.slack_url,
                              slack_emoji=self.config.slack_emoji,
                              event='built',
                              service_name=self.config.api_service_name or self.config.service_name,
                              deployment_host=connection.host,
                              deployment_user=self.config.user)

    # Interface

    def upload(self, connection):
        raise NotImplementedError("Must be implemented in subclasses")

    def install(self, connection):
        """
        [advanced]\tinstall latest build on the hosts you specify
        """
        raise NotImplementedError("Must be implemented in subclasses")

    def rollback(self, connection):
        """
        [core]\t\tchoose a version to rollback to from all available releases
        """
        raise NotImplementedError("Must be implemented in subclasses")

    def _get_bundle_name(self, connection):
        raise NotImplementedError("Must be implemented in subclasses")

    # common/shared methods

    def tail(self, connection, log_name="output.log"):
        """
        [core]\tTail log on the remote host
        :param: connection: Connection
        :param: log_name: str name of log file
        """
        try:
            connection.sudo(f'tail -f /var/log/{self.config.service_name}/{log_name}', user=self.config.user)
        finally:
            sys.exit()

    def service_wrapper(self, connection, cmd, print_output=True, warn_only=False):
        """
        [core]\tRun service commands on the remote hosts such as `start', 'stop', 'restart', 'status'
        Needs to be ported to systemctl
        :param: connection: Connection
        :param: cmd: str command to run. Command must be whitelisted
        :return str output of command
        """
        allowed = ('start', 'stop', 'restart', 'status')
        if cmd not in allowed:
            print(red('unknown command, try one of %s' % ','.join(allowed)))
            sys.exit(1)

        linux_version = 0.0
        try:
            release = connection.run('lsb_release -a | grep Release', hide='both')
            linux_args = release.stdout.split()
            linux_version = float(linux_args[1])
            service_mgmt = 'systemd' if linux_version >= 16 else 'upstart'
            print(f"Linux version is {linux_version}, using {service_mgmt}")
        except Exception as e:
            print(f"Unable to determine linux version ({str(e)}), assuming `upstart`")

        if linux_version >= 16:
            if print_output:
                print(blue(f'executing systemd:{cmd}'))
            result = connection.run(f"sudo systemctl {cmd} {self.config.service_name} --no-pager",
                                    warn=warn_only,
                                    hide='both')
        else:
            if print_output:
                print(blue(f'executing init:{cmd}'))
            result = connection.run(f"sudo service {self.config.service_name} {cmd}",
                                    warn=warn_only,
                                    hide='both')
        out = result.stdout
        if print_output and out:
            print(green(out))
        return out

    def link_latest_release(self, connection):
        """
        [advanced]\t"Cowboy" deploy - switch symlink of release folder to the most recent one
        :param: connection: Connection
        :return: nothing
        """
        release_dir = self._get_latest_release(connection)
        print(green("Linking release %s into current" % magenta(release_dir)))
        self._change_symlink_to(connection, self._rpath('releases', release_dir))

    def _get_latest_release(self, connection):
        """
        Get latest release dir in the releases dir
        :param connection: Connection
        :return: str name of dir of latest release
        """
        result = connection.run('ls -lt %s' % self._rpath('releases'), hide='both')
        return result.stdout.split('\n')[1].split()[-1]

    def _start_or_restart(self, connection):
        """
        Start service on the remote host
        If already started, stop it first, then start it.
        :param connection: Connection
        :return: nothing
        """
        if self.config.use_init or self.config.use_upstart:
            if self._is_running(connection):
                print(green(f'Restarting {self.config.service_name} on {connection.host}'))
                self.service_wrapper(connection, 'stop')
                self.service_wrapper(connection, 'start')
            else:
                print(green(f'Starting {self.config.service_name} on {connection.host}'))
                self.service_wrapper(connection, 'start')

    def _is_running(self, connection):
        """
        Check if service is running on the remote host
        :param connection: Connection
        :return: bool whether service is running
        """
        result = self.service_wrapper(connection, 'status', print_output=False, warn_only=False)
        return 'start/running' in result or 'active (running)' in result

    def _lpath(self, *args):
        """
        Local path
        :param args: optional strs to append to path
        :return: str path
        """
        return os.path.join(self.config.cwd, *args)

    def _rpath(self, *args):
        """
        Remote path
        :param args: optional strs to append to path
        :return: str path
        """
        return os.path.join(self.config.service_root, *args)

    def _tpath(self, *args):
        """
        Temp path
        :param args:  optional strs to append to path
        :return: str path
        """
        return os.path.join('/tmp', *args)

    def _create_if_missing(self, connection, path):
        """
        Given a path to a directory, create it if does not exist
        :param connection: Connection
        :param path: path to directory
        :return: Nothing
        """
        if not exists(connection, path):
            connection.sudo(f'mkdir -p {path}',
                            user=self.config.user,
                            hide='stdout')  # Note: skipping group

    def _change_symlink_to(self, connection, release_path):
        """
        Symlink `current` dir to given release
        :param connection: Connection
        :param release_path: str release dir to symlink to
        :return: nothing
        """
        releases = self._rpath()
        print(blue("Linking release %s into current" % release_path))
        connection.sudo(f'ln -sfT {release_path} {releases}/current',
                        user=self.config.user)  # Note: skipping group

    def _log_error_and_exit(self, connection, message):
        """
        Report errors and exit any current tasks
        :param connection: Connection
        :param message: str
        :return: nothing
        """
        print(red(message))
        print(red('Aborting deployment'))
        track_event_slack(slack_url=self.config.slack_url,
                          slack_emoji=self.config.slack_emoji,
                          event=message,
                          service_name=self.config.api_service_name or self.config.service_name,
                          deployment_host=connection.host,
                          deployment_user=self.config.user,
                          failure=True)
        sys.exit(1)

    def _get_commit_hash(self, connection, shorten=False):
        """
        Obtain commit hash that the repository is currently at, so we can tag the release dir with it as well
        as report the commit hash of what's deployed. Note that this is not the "latest" commit intentionally, it is the
        commit hash that the repository is currently pointed to.
        :param connection: Connection
        :param shorten: bool short or full commit hash
        :return: str commit hash, ex. `f333c776c8cf9d56a4604ff29640326f50f00c19`
        """
        if shorten:
            result = connection.local('git rev-parse --short=7 HEAD', hide='stdout')
        else:
            result = connection.local('git rev-parse HEAD', hide='stdout')

        if result.failed or result.stdout.strip() == '':
            self._log_error_and_exit(connection, "failed to obtain commit hash")

        return result.stdout.strip()

    def _new_release_dir(self, connection):
        """
        Generate a new release dir for the remote hosts, this needs to be the same across hosts
        to make it clearer that they all have the same release/build. yes this is semi-brittle,
        but for most situations it should be adequate.
        :return: str release dir
        """
        timestamp = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        commit_hash = self._get_commit_hash(connection)

        return f'{timestamp}-{self.config.deployment_user}-{commit_hash}'

    def _get_current_release(self, connection):
        """
        Get name of the current release on the remote host
        :param connection: Connection
        :return: str dir name of the release
        """
        result = connection.sudo('readlink %s' % self._rpath('current'),
                                 user=self.config.user)  # note: had to take out group=self.config.group
        current_release = result.stdout.split('/')[-1].strip()
        return current_release

    def _track_event(self, connection, event):
        """
        Dispatch deploy/failure events across third party systems
        :param connection: Connection object
        :param event: string event name
        :return: nothing
        """
        track_event_graphite(graphite_host=self.config.graphite_host,
                             event=event,
                             service_name=self.config.api_service_name or self.config.service_name,
                             deployment_host=connection.host,
                             deployment_user=self.config.deployment_user)
        track_event_api(track_event_endpoint=self.config.track_event_endpoint,
                        event=event,
                        service_name=self.config.api_service_name or self.config.service_name,
                        deployment_host=connection.host,
                        deployment_user=self.config.deployment_user)
        track_event_slack(slack_url=self.config.slack_url,
                          slack_emoji=self.config.slack_emoji,
                          event=event,
                          commit_hash=self._get_commit_hash(connection, shorten=True),
                          project_version=self.project_version,
                          service_name=self.config.api_service_name or self.config.service_name,
                          deployment_host=connection.host,
                          deployment_user=self.config.deployment_user)
