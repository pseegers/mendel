"""
# Houses the main Mendel class, which coordinates deployment across hosts,
# provided a configuration.
# TODO drop a file into release directories that are "successful"
# TODO so we don't roll back to a failed build. either that or we cleanup after
# TODO ourselves
"""

import argparse
import sys

from fabric.tasks import Task

from mendel.util.colors import blue
from mendel.util.colors import red
from .deployer.deb import DebDeployer
from .deployer.jar import JarDeployer
from .deployer.remote_deb import RemoteDebDeployer
from .deployer.remote_jar import RemoteJarDeployer
from .deployer.tgz import TarballDeployer


class Mendel(object):
    DEPLOYER_MAP = {
        'tgz': TarballDeployer,
        'deb': DebDeployer,
        'jar': JarDeployer,
        'remote_deb': RemoteDebDeployer,
        'remote_jar': RemoteJarDeployer,
        None: RemoteJarDeployer  # Default. Can reassess having this later
    }
    """
    A class for managing service deployments

    Instantiate a Mendel instance in your fabfile,
    and then delegate to it to perform tasks.

        #fabfile.py

        from mendel import Mendel

        mendel = Mendel(service_name='my-service')

        @task
        def deploy():
            mendel.deploy()

        @task
        def upload():
            mendel.upload()


    Fabric will also automatically discover any
    Task instances in your fabfile, so you can use
    tasks property to instantiate all of them
    """

    def __init__(self, config, hosts=None):
        super().__init__()
        self.bundle_type = config.bundle_type
        self.deployer = self.DEPLOYER_MAP[self.bundle_type](service_name=config.service_name, config=config)
        # Define target hosts
        # Option a) provide hosts in the constructor
        self.hosts = hosts
        # Option b) provide hosts given at command line and reconcile with those in config
        if not self.hosts:
            parser = argparse.ArgumentParser(add_help=False)
            parser.add_argument('-H', '--hosts', default=None)
            options, _ = parser.parse_known_args()
            if options and options.hosts:
                self.hosts = options.hosts
        # Option c) provide hosts in the config, and at runtime (`fab` or `mendel` specific the hosts alias)
        if not self.hosts:
            for environment_name, environment in config.available_host_groups.items():
                if environment_name in sys.argv:
                    self.hosts = environment.to_connection_dicts()

        if self.hosts:
            # 3. Instantiate Mendel
            print(blue(f"Using {self.hosts} as hosts"))
        elif any(arg.endswith('fab') for arg in sys.argv):
            # mendel is being used as a lib for fab, so we don't need to complain about hosts, fab will
            pass
        else:
            print(red(f"You must specify hosts for your tasks!"))
            sys.exit(1)

    def __call__(self, task_name, *args, **kwargs):
        task = getattr(self.deployer, task_name, None)
        if task:
            task(*args, **kwargs)
        else:
            import inspect
            tasks = inspect.getmembers(self, predicate=inspect.ismethod)
            print(red("Invalid task name: %s" % task_name))
            print()
            print("Please choose one of")
            print()
            for task, _ in tasks:
                if not task.startswith("_"):
                    print("\t" + task)

    @property
    def tasks(self):
        """
        Generate Fabric Task instances for each of the Mendel functionalities
        :return: list of Task instances
        """
        methods = [
            self.deployer.upload,
            self.deployer.deploy,
            self.deployer.install,
            self.deployer.build,
            self.deployer.tail,
            self.deployer.rollback,
            self.deployer.service_wrapper,
            self.deployer.link_latest_release
        ]

        # todo do we need to cd into cwd on each of theses tasks?
        return [Task(hosts=self.hosts, body=m) for m in methods]
