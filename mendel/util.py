import argparse
import sys

import yaml
from fabric.api import env
from fabric.api import lcd
from fabric.colors import red
from fabric.colors import yellow, green
from fabric.tasks import WrappedCallableTask


def stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()


def warn(s):
    stderr(yellow(s))


def create_host_task(key, host_config):
    """ Generate host tasks dynamically from config """

    # do validation *before* dynamic task function generation
    # allowing for hostname to avoid a breaking change
    if 'hostname' in host_config and 'hostnames' in host_config:
        raise ValueError(red('cannot specify both \'hostname\' and \'hostnames\''))
    if 'hostname' not in host_config and 'hostnames' not in host_config:
        raise ValueError(red('must supply \'hostnames\' section'))

    hosts_key = 'hostname' if 'hostname' in host_config else 'hostnames'

    def f():
        hosts = None
        if 'hostname' in host_config:
            warn('\'hostname\' is being deprecated in favor of \'hostnames\' so you can provide a csv-list\n')
            hostname = host_config['hostname']
            hosts = [hostname]

        if 'hostnames' in host_config:
            hosts = [h.strip() for h in host_config['hostnames'].split(',')]

        env.hosts = hosts
        env.port = host_config.get('port', 22)

        # convenience for local deployment to Vagrantfile VM
        if hosts[0] in {'localhost', '127.0.0.1'}:
            hostname = '127.0.0.1'  # sometimes fabric just fails with 'localhost'
            env.user = 'vagrant'
            env.password = 'vagrant'
            env.port = host_config.get('port', 2222)

    f.__name__ = key
    f.__doc__ = "[hosts] \tsets deploy hosts to %s" % green(host_config[hosts_key])
    return WrappedCallableTask(f)

def lcd_task(task, cd_to):
    """
    wrap a function so that it will be
    executed in a specific directory on
    the host machine

    uses `fabric.api.lcd(dest)`

    the returned function will have the same
    __name__ and __doc__ as the input `task`


    :param task: the function to execute
    :param cd_to: the directory in which to execute
    :return: a function that will be executed in `cd_to`
    """
    def func(*args, **kwargs):
        with lcd(cd_to):
            task(*args, **kwargs)

    func.__name__ = task.__name__
    func.__doc__ = task.__doc__
    return func


class ConfigMissingError(Exception):
    """
    raised when mendel configuration is missing or malformed
    """
    pass


def load_mendel_config():
    """
    load the config from `mendel.yml`, or from the
    argument of command line flag `-f` or `--file`

    :return: configuration as a dictionary
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-f', '--file', default='mendel.yml')
    options, args = parser.parse_known_args()
    try:
        with open(options.file) as f:
            config = yaml.load(f)
            return config, options.file
    except Exception as e:
        raise ConfigMissingError(
            red('%(fn)s not found or malformed. '
                'To use the mendel cli, please '
                'include service info in %(fn)s' % dict(fn=options.file)))
