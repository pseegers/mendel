import sys
from collections import OrderedDict

import yaml

from mendel.util.colors import red


def order_rep(dumper, data):
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', data.items(), flow_style=False)


yaml.add_representer(OrderedDict, order_rep)


def init(connection, service_name=None, bundle_type=None, project_type=None):
    """
    [core]\t\tPrepare an existing project to be deployed by mendel.
    """
    # NOTE: this is to side-step our eventual desire to use the sprout_java cookbook here.

    # TODO parse pom.xml's artifactId as sane default?
    service_name = service_name or input('enter service name: ')
    if not service_name:
        print(red('you must provide a service_name'))
        sys.exit(1)

    bundle_type = bundle_type or input(
        'enter bundle_type type (jar, tgz, deb, remote_jar) [remote_jar]: ') or 'remote_jar'
    if bundle_type not in ('jar', 'tgz', 'deb', 'remote_jar'):
        print(red('if you want bundle_type %s, issue a pull request.' % bundle_type))
        sys.exit(1)

    if bundle_type in ('jar', 'deb', 'remote_jar'):
        # default for jar or deb packaging should just be target, this is expected
        # for most people's builds.
        build_target_path = 'target/'
    else:
        build_target_path = 'target/%s' % service_name

    project_type = project_type or input('enter project_type type (java, python) [java]: ') or 'java'
    if project_type not in ('java', 'python'):
        print(red('if you want project_type %s, issue a pull request.' % bundle_type))
        sys.exit(1)
    if project_type == 'python' and bundle_type != 'tgz':
        print(red('if you want project_type {} to use {}, issue a pull request.'.format(project_type, bundle_type)))
        sys.exit(1)

    conf = OrderedDict()
    conf['service_name'] = service_name
    conf['bundle_type'] = bundle_type
    conf['project_type'] = project_type
    conf['build_target_path'] = build_target_path
    conf['hosts'] = {'dev': {'hostnames': '127.0.0.1', 'port': '2222'}}
    with open('mendel.yml', 'w') as f:
        yaml.dump(conf, f, default_flow_style=False)
