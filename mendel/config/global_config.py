"""
Encapsulate parsing and behavior of the mendel configuration file
which governs mendel behavior and defaults across all services
"""
import os

from configparser import SafeConfigParser
from configparser import NoSectionError
from configparser import NoOptionError


class Parser(SafeConfigParser):

    def get_or(self, section, option, default=None):
        try:
            return self.get(section, option)
        except (NoSectionError, NoOptionError):
            return default

    def getint_or(self, section, option, default=None):
        try:
            return self.getint(section, option)
        except (NoSectionError, NoOptionError):
            return default


class GlobalConfig(object):

    def __init__(self):
        self.config_file = os.environ.get('MENDEL_CONFIG_FILE', os.path.expanduser('~/.mendel.conf'))
        self._parser = Parser()

        # load config file
        # works at least on OS X and Linux; not sure about Windows
        if os.path.isfile(self.config_file):
            with open(self.config_file) as f:
                self._parser.read_file(f)

        self.GLOBAL_NEXUS_USER = os.environ.get('MENDEL_NEXUS_USER', self._parser.get_or('nexus', 'user'))
        self.GLOBAL_NEXUS_HOST = os.environ.get('MENDEL_NEXUS_HOST', self._parser.get_or('nexus', 'host'))
        self.GLOBAL_NEXUS_PORT = int(os.environ.get('MENDEL_NEXUS_PORT', self._parser.getint_or('nexus', 'port', 0)))
        self.GLOBAL_NEXUS_REPOSITORY = os.environ.get(
            'MENDEL_NEXUS_REPOSITORY', self._parser.get_or(
                'nexus', 'repository'))
        self.GLOBAL_GRAPHITE_HOST = os.environ.get('MENDEL_GRAPHITE_HOST', self._parser.get_or('graphite', 'host'))
        self.GLOBAL_TRACK_EVENT_ENDPOINT = os.environ.get(
            'TRACK_EVENT_ENDPOINT', self._parser.get_or('api', 'track_event'))
        self.GLOBAL_DEPLOYMENT_USER = os.environ.get('DEPLOYMENT_USER', self._parser.get_or('deployment', 'user'))

    def __str__(self):
        return "Mendel GlobalConfig object using %s" % self.config_file

    def __repr__(self):
        return "Mendel GlobalConfig object using %s" % self.config_file
