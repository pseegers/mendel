import os

from ConfigParser import SafeConfigParser
from ConfigParser import NoSectionError
from ConfigParser import NoOptionError


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


class Config(object):

    def __init__(self):
        config_file = os.environ.get('MENDEL_CONFIG_FILE', os.path.expanduser('~/.mendel.conf'))
        self._parser = Parser()

        # load config file
        # works at least on OS X and Linux; not sure about Windows
        if os.path.isfile(config_file):
            with open(config_file) as f:
                self._parser.readfp(f)

        self.NEXUS_USER = os.environ.get('MENDEL_NEXUS_USER', self._parser.get_or('nexus', 'user'))
        self.NEXUS_HOST = os.environ.get('MENDEL_NEXUS_HOST', self._parser.get_or('nexus', 'host'))
        self.NEXUS_PORT = int(os.environ.get('MENDEL_NEXUS_PORT', self._parser.getint_or('nexus', 'port', 0)))
        self.NEXUS_REPOSITORY = os.environ.get('MENDEL_NEXUS_REPOSITORY', self._parser.get_or('nexus', 'repository'))
        self.GRAPHITE_HOST = os.environ.get('MENDEL_GRAPHITE_HOST', self._parser.get_or('graphite', 'host'))
        self.TRACK_EVENT_ENDPOINT = os.environ.get('TRACK_EVENT_ENDPOINT', self._parser.get_or('api', 'track_event'))
