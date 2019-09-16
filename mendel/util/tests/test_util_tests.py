from unittest import TestCase


from mendel.util.misc import str_to_bool


class MendelConfigValidationTests(TestCase):

    def test_can_convert_upstart_from_string_to_bool(self):
        for val in ("y", "yes", "t", "true", "on", "1", " YES "):
            self.assertTrue(str_to_bool(val))
        for val in ("n", "no", "f", "false", "off", "0", " NO "):
            self.assertFalse(str_to_bool(val))
