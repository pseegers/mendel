import os
import sys
import yaml
from collections import OrderedDict

from fabric.colors import red, green, blue, magenta
from fabric.api import env
from fabric.api import task

from mendel.core import Mendel
from mendel.util import create_host_task
from mendel.util import ConfigMissingError
from mendel.util import is_running_tests
from mendel.util import load_mendel_config


env.colorize_errors = True
env.use_ssh_config = True


def order_rep(dumper, data):
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', data.items(), flow_style=False)
yaml.add_representer(OrderedDict, order_rep)


@task
def init(service_name=None, bundle_type=None, project_type=None):
    """
    [core]\t\tPrepare an existing project to be deployed by mendel.
    """
    # NOTE: this is to side-step our eventual desire to use the sprout_java cookbook here.

    # TODO parse pom.xml's artifactId as sane default?
    service_name = service_name or raw_input('enter service name: ')
    if not service_name:
        red('you must provide a service_name')
        sys.exit(1)

    bundle_type = bundle_type or raw_input('enter bundle_type type (jar, tgz, deb) [jar]: ') or 'jar'
    if bundle_type not in ('jar', 'tgz', 'deb'):
        red('if you want bundle_type %s, issue a pull request.' % bundle_type)
        sys.exit(1)

    if bundle_type in ('jar', 'deb'):
        # default for jar or deb packaging should just be target, this is expected
        # for most people's builds.
        build_target_path = 'target/'
    else:
        build_target_path = 'target/%s' % service_name

    project_type = project_type or raw_input('enter project_type type (java, python) [java]: ') or 'java'
    if project_type not in ('java', 'python'):
        red('if you want project_type %s, issue a pull request.' % bundle_type)
        sys.exit(1)
    if project_type == 'python' and bundle_type != 'tgz':
        red('if you want project_type {} to use {}, issue a pull request.'.format(project_type, bundle_type))
        sys.exit(1)

    conf = OrderedDict()
    conf['service_name'] = service_name
    conf['bundle_type'] = bundle_type
    conf['project_type'] = project_type
    conf['build_target_path'] = build_target_path
    conf['hosts'] = {'dev': {'hostnames': '127.0.0.1', 'port': '2222'}}
    with open('mendel.yml', 'w') as f:
        yaml.dump(conf, f, default_flow_style=False)

    # TODO generate stock vagrant file
    # other misc stuff to get LWRP-type env


if not is_running_tests():
    ############################################################################
    # must be outside of a main block to work, happens upon import of this file
    # cuz fabric is magic.
    ############################################################################
    try:
        # TODO so much error handing
        config, config_file = load_mendel_config()

        mendel_yaml_abspath = os.path.abspath(config_file)
        config['cwd'] = os.path.dirname(mendel_yaml_abspath)
        print blue('Using config at %s' % magenta(mendel_yaml_abspath))
        print blue('Setting working directory to %s' % magenta(config['cwd']))

        d = Mendel(**config)

        upload, deploy, install, build, tail, rollback, upstart, link_latest_release = d.get_tasks()

        for key, host_string in config.get('hosts', {}).items():
            vars()[key] = create_host_task(key, host_string)
    except ConfigMissingError as e:
        if 'fab' in sys.argv:
            # mendel is being used as a lib for fab, so we don't need a config
            pass
        elif len(sys.argv) >= 2 and ('mendel' in sys.argv[0] and 'init' in sys.argv[1]):
            # mendel is being used as tool to bootstrap a project, so we don't need a config
            pass
        else:
            print red(e.message)
            print
            print green('if you\'re bootstrapping a project, use `mendel init`')
            sys.exit(1)
    except Exception as e:

        print red(e.message)
        # don't let it continue and spit out the fabric usage
        # stuff if we can't properly parse the mendel.yml
        sys.exit(1)
