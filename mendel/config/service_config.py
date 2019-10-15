"""
Encapsulate parsing and behavior of the `mendelfile` config which is defined for each service
governs mendel behavior for that specific service
"""
import argparse
import getpass
import os

import yaml

from mendel.util.colors import red
from mendel.util.colors import yellow
from mendel.util.misc import str_to_bool
from .global_config import GlobalConfig
from fabric.tasks import Task


class ConfigMissingError(Exception):
    """
    raised when mendel configuration is missing or malformed
    """
    pass


class ServiceConfig(GlobalConfig):
    DEFAULT_SLACK_EMOJI = ":rocket:"
    DEFAULT_CWD = "."
    DEFAULT_BUNDLE_TYPE = "remote_jar"
    DEFAULT_PROJECT_TYPE = "java"
    DEFAULT_VERSION_CONTROL = "git"

    def __init__(self, **kwargs):
        """
        House default config attributes not overridden by service config
        :param service_name: str service name
        """
        super().__init__()
        self.service_name = kwargs.get('service_name')
        self.api_service_name = kwargs.get('api_service_name') or self.service_name
        if self.service_name:
            self.service_root = kwargs.get('service_root') or os.path.join('/srv', self.service_name)
            self.build_target_path = kwargs.get('build_target_path') or 'target/' + self.service_name
        else:
            self.service_root = kwargs.get('service_root')
            self.build_target_path = kwargs.get('build_target_path')
        self.user = kwargs.get('user') or self.service_name
        self.deployment_user = kwargs.get('deployment_user') or self.GLOBAL_DEPLOYMENT_USER or getpass.getuser()
        self.group = kwargs.get('group') or self.user or self.service_name
        self.bundle_type = kwargs.get('bundle_type') or self.DEFAULT_BUNDLE_TYPE
        self.project_type = kwargs.get('project_type') or self.DEFAULT_PROJECT_TYPE
        self.cwd = kwargs.get('cwd') or self.DEFAULT_CWD
        self.jar_name = kwargs.get('jar_name') or self.service_name
        self.classifier = kwargs.get('classifier')
        self.version_control = kwargs.get('version_control') or self.DEFAULT_VERSION_CONTROL
        self.nexus_user = kwargs.get('nexus_user') or self.GLOBAL_NEXUS_USER
        self.nexus_host = kwargs.get('nexus_host') or self.GLOBAL_NEXUS_HOST
        self.nexus_port = kwargs.get('nexus_port') or self.GLOBAL_NEXUS_PORT
        self.nexus_repository = kwargs.get('nexus_repository') or self.GLOBAL_NEXUS_REPOSITORY
        self.graphite_host = kwargs.get('graphite_host') or self.GLOBAL_GRAPHITE_HOST
        self.slack_url = kwargs.get('slack_url')
        self.slack_emoji = kwargs.get('slack_emoji') or self.DEFAULT_SLACK_EMOJI
        self.track_event_endpoint = kwargs.get('track_event_endpoint') or self.GLOBAL_TRACK_EVENT_ENDPOINT
        self.host_configs = kwargs.get('host_configs') or []
        self.use_init = False
        self.use_upstart = True

    @classmethod
    def from_dict(cls, dict_config: dict):
        """
        Take a config dict (usually derived from a yml) and process into a config object
        :param dict_config: dict config
        :return: instance of ServiceConfig
        """
        config = ServiceConfig(service_name=dict_config['service_name'])

        # Attrs that are conditionally constructed
        config.service_root = dict_config.get('service_root') or os.path.join('/srv', dict_config['service_name'])
        config.build_target_path = dict_config.get('build_target_path') or 'target/' + dict_config['service_name']
        config.jar_name = dict_config.get('jar_name') or dict_config['service_name']
        config.user = dict_config.get('user') or dict_config['service_name']
        config.api_service_name = dict_config.get('api_service_name') or dict_config['service_name']
        config.group = dict_config.get('group') or config.user or dict_config['service_name']

        # Attrs that are simply set if they are present
        simple_attrs = ['bundle_type', 'project_type', 'cwd', 'classifier', 'nexus_user', 'nexus_host', 'nexus_port',
                        'nexus_repository', 'graphite_host', 'slack_url', 'slack_emoji']
        for attr in simple_attrs:
            if dict_config.get(attr):
                setattr(config, attr, dict_config[attr])

        host_groups = dict_config.get('hosts', {})
        if host_groups:
            config.host_configs = ServiceConfig._process_host_configs(host_groups)

        use_upstart = dict_config.get('use_upstart')
        use_init = dict_config.get('use_init')
        if isinstance(use_init, str):
            config.use_init = str_to_bool(use_init)
        else:
            config.use_init = use_init

        if not use_init:
            if isinstance(use_upstart, str) and use_upstart.lower() == 'false':
                print(red("DEPRECATION WARNING: use_upstart must be changed to use_init."))
                config.use_init = True
                config.use_upstart = False
            elif use_upstart is False:
                print(red("DEPRECATION WARNING: use_upstart must be changed to use_init."))
                config.use_init = True
                config.use_upstart = False
            elif use_upstart is None:
                # If use_init is explicitly False and use_upstart is unset, disable upstart
                config.use_upstart = False
            else:
                config.use_init = False
                config.use_upstart = True

        return config

    @staticmethod
    def _process_host_configs(host_groups):
        """
        Process host settings from config
        :param host_groups: dict from mendel config's `hosts`
        :return: list of HostConfig instances
        """
        host_configs = []
        for group_name, host_config in host_groups.items():
            if 'hostname' in host_config and 'hostnames' in host_config:
                raise ValueError(red('cannot specify both \'hostname\' and \'hostnames\''))
            if 'hostname' not in host_config and 'hostnames' not in host_config:
                raise ValueError(red('must supply \'hostnames\' section'))
            port = host_config.get('port', 22)
            hostnames = []
            if 'hostname' in host_config:
                print(yellow('\'hostname\' is being deprecated in favor of \'hostnames\' so you can provide a csv-list\n'))
                hostname = host_config['hostname']
                hostnames = [hostname]
            if 'hostnames' in host_config:
                hostnames = [h.strip() for h in host_config['hostnames'].split(',')]

            host_configs.append(HostConfig(name=group_name, hosts=hostnames, port=port))
        return host_configs

    @property
    def available_host_groups(self):
        return {h.name: h for h in self.host_configs if self.host_configs}

    @property
    def host_tasks(self):
        """
        Create a list of fabric Tasks for each deployment environment
        These tasks are empty shells, they don't do anything
        They are in place to appease Fabric at runtime.
        :return: list of Task instances
        """
        tasks = []
        for k in self.available_host_groups.keys():
            def f(c): return None
            f.__name__ = k
            tasks.append(Task(body=f))
        return tasks

    def __str__(self):
        return "Mendel ServiceConfig object for %s" % self.service_name

    def __repr__(self):
        return "Mendel ServiceConfig object for %s" % self.service_name


def load_mendel_config() -> (ServiceConfig, str):
    """
    Load the config from `mendel.yml`, or from the
    argument of command line flag `-f` or `--file`

    :return: configuration as a dictionary
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-f', '--file', default='mendel.yml')
    options, args = parser.parse_known_args()
    try:
        with open(options.file) as f:
            config = yaml.safe_load(f)

        return ServiceConfig.from_dict(dict_config=config), options.file
    except Exception as e:
        print(red(str(e)))
        raise ConfigMissingError(
            red('%(fn)s not found or malformed. '
                'To use the mendel cli, please '
                'include service info in %(fn)s' % dict(fn=options.file)))


class HostConfig(object):
    """
    Encapsulate configuration of deployment to a group of servers, such as `prod` or `stage`
    """

    def __init__(self, name, hosts, port=22):
        super().__init__()
        self.name = name
        self.hosts = hosts
        self.port = port

    def __repr__(self):
        return "Mendel HostConfig for %s: Hosts %s" % (self.name, self.hosts)

    def __str__(self):
        return "Mendel HostConfig for %s: Hosts %s" % (self.name, self.hosts)

    def to_connection_dicts(self):
        """
        Convert HostConfig to 1 or more dicts that Fabric 2.0+ accepts as a "connection context"
        1 connection context for each host
        :return: list of dicts compatible to be used by Invoke/Fabric as Contexts
        """
        connections = []
        for host in self.hosts:
            connections.append(dict(host=host, port=self.port))
        return connections

    def to_fab_task(self):
        def f(c): return None
        f.__name__ = self.name
        return Task(body=f)
