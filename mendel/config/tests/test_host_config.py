from unittest import TestCase

from mendel.config.service_config import ServiceConfig


class HostConfigTests(TestCase):
    def setUp(self):
        super().setUp()

    def test_host_and_hostnames(self):
        hosts = {
            'prod': {
                'hostname': 'host-01',
                'hostnames': 'host-01,host-02'
            }
        }
        with self.assertRaises(ValueError):
            ServiceConfig._process_host_configs(hosts)

    def test_must_have_hostname_or_hostnames(self):
        hosts = {
            'prod': {}
        }
        with self.assertRaises(ValueError):
            ServiceConfig._process_host_configs(hosts)

    def test_hostnames_one(self):
        hosts = {
            'prod': {
                'hostnames': 'prod-host-01,prod-host-02'
            }
        }
        configs = ServiceConfig._process_host_configs(hosts)
        self.assertEqual(len(configs), 1)
        config = configs[0]
        self.assertEqual(config.name, 'prod')
        self.assertEqual(config.port, 22)
        self.assertEqual(set(config.hosts), {'prod-host-01', 'prod-host-02'})

    def test_to_connection_dicts(self):
        hosts = {
            'prod': {
                'hostnames': 'prod-host-01,prod-host-02'
            }
        }
        configs = ServiceConfig._process_host_configs(hosts)
        self.assertEqual(len(configs), 1)
        config = configs[0]
        dicts = config.to_connection_dicts()
        self.assertEqual(len(dicts), 2)
        self.assertEqual(dicts[0]['host'], 'prod-host-01')
        self.assertEqual(dicts[0]['port'], 22)
        self.assertEqual(dicts[1]['host'], 'prod-host-02')
        self.assertEqual(dicts[1]['port'], 22)

    def test_hostnames_multiple(self):
        hosts = {
            'prod': {
                'hostnames': 'prod-host-01,prod-host-02'
            },
            'dev': {
                'hostnames': '127.0.0.1',
                'port': '2200'
            }
        }
        configs = ServiceConfig._process_host_configs(hosts)
        self.assertEqual(len(configs), 2)
        config = configs[0]
        self.assertEqual(config.name, 'prod')
        self.assertEqual(config.port, 22)
        self.assertEqual(set(config.hosts), {'prod-host-01', 'prod-host-02'})
        config_2 = configs[1]
        self.assertEqual(config_2.name, 'dev')
        self.assertEqual(config_2.port, '2200')
        self.assertEqual(set(config_2.hosts), {'127.0.0.1'})

    def test_hostname(self):
        hosts = {
            'prod': {
                'hostname': 'prod-host-01'
            }
        }
        configs = ServiceConfig._process_host_configs(hosts)
        self.assertEqual(len(configs), 1)
        config = configs[0]
        self.assertEqual(config.name, 'prod')
        self.assertEqual(config.port, 22)
        self.assertEqual(set(config.hosts), {'prod-host-01'})
