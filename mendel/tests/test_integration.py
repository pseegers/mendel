from subprocess import PIPE
from subprocess import Popen
from unittest import TestCase
import os
import urllib2

import time


MENDEL_TEST_FILE = 'mendel.test.yml'
MENDEL_TGZ_YAML = """
service_name: myservice
bundle_type: tgz
project_type: java
hosts:
  dev:
    hostnames: 127.0.0.1
    port: %s
"""


class IntegrationTests(TestCase):

    def setUp(self):
        print os.environ.keys()
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.workingdir = os.path.join(curdir, '..', '..', 'examples', 'java', 'tgz')
        fileloc = os.path.join(self.workingdir, MENDEL_TEST_FILE)
        ssh_port = os.environ.get('STANTONK/FAT-CONTAINER_22_TCP')
        with open(fileloc, 'wb') as f:
            filecontents = MENDEL_TGZ_YAML % ssh_port
            print filecontents
            f.write(filecontents)

    def test_tgz_mendel_deploy(self):
        cmdline = 'mendel -f %s dev deploy' % MENDEL_TEST_FILE
        print cmdline
        p = Popen(cmdline, stdout=PIPE, shell=True, cwd=self.workingdir)
        p.wait()
        out, err = p.communicate()
        print out
        print err

        myservice_http_port = os.environ.get('STANTONK/FAT-CONTAINER_8080_TCP')
        url = 'http://127.0.0.1:%s/hello' % myservice_http_port
        print url

        # give the java service a few seconds to come up
        status_code, content = 0, ''
        for retries in range(0, 5):
            try:
                r = urllib2.urlopen(url)
                content = r.read()
                status_code = r.getcode()
                # r = requests.get(url)
                # status_code, content = r.status_code, r.content
            except:
                pass
            time.sleep(2)

        self.assertEqual(200, status_code)
        self.assertIn('Hello', content)

    def tearDown(self):
        os.remove(os.path.join(self.workingdir, MENDEL_TEST_FILE))
