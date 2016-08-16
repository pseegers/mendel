from unittest import TestCase

from mendel.util import create_host_task
from mendel.util import str_to_bool


class MendelConfigValidationTest(TestCase):

    def test_cannot_use_both_hostname_and_hostnames(self):
        self.assertRaises(ValueError, create_host_task, 'prod', {'hostname': 'blah', 'hostnames': 'blah,blah2'})

    def test_must_have_hostname_or_hostnames(self):
        self.assertRaises(ValueError, create_host_task, 'prod', {})

    def test_can_convert_upstart_from_string_to_bool(self):
        for val in ('y', 'yes', 't', 'true', 'on', '1'):
            self.assertTrue(str_to_bool(val))
        for val in ('n', 'no', 'f', 'false', 'off', '0'):
            self.assertFalse(str_to_bool(val))
