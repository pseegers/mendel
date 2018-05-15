from subprocess import PIPE
from subprocess import Popen
from unittest import TestCase
import os
import urllib2
from fabric import state
from fabric import operations
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

MENDEL_JAR_YAML = """
service_name: myservice
bundle_type: jar
project_type: java
build_target_path: target/
hosts:
  dev:
    hostnames: 127.0.0.1
    port: %s
"""

# class TgzIntegrationTests(TestCase):
#
#     def setUp(self):
#         print os.environ.keys()
#         curdir = os.path.dirname(os.path.abspath(__file__))
#
#         self.workingdir = os.path.join(curdir, '..', '..', 'examples', 'java', 'tgz')
#         fileloc = os.path.join(self.workingdir, MENDEL_TEST_FILE)
#         self.ssh_port = os.environ.get('STANTONK/FAT-CONTAINER_22_TCP')
#
#         print "SSH PORT: %s" % self.ssh_port
#         with open(fileloc, 'wb') as f:
#             filecontents = MENDEL_TGZ_YAML % self.ssh_port
#             print filecontents
#             f.write(filecontents)
#
#     def test_tgz_mendel_deploy(self):
#         (status_code, content) = self.do_deploy()
#         print "status code: %s" % status_code
#         print "content: %s" % content
#         self.assertEqual(200, status_code)
#         self.assertIn('Hello', content)
#
#     def test_upstart_config_changes(self):
#         state.env.user = 'vagrant'
#         state.env.password = 'vagrant'
#         state.env.host_string = 'localhost:%s' % self.ssh_port
#         self.do_deploy()
#         pre_config_status = operations.run("ps aux | grep myservice | grep changed_config | grep -v grep", warn_only=True)
#         self.assertTrue(pre_config_status.failed) # grep returns nonzero if it doesn't find the string
#         operations.sudo("sed -i 's/-jar/-Dchanged_config_line=true -jar/;' /etc/init/myservice.conf")
#         self.do_deploy()
#         config_status = operations.run("ps aux | grep myservice | grep changed_config | grep -v grep")
#         self.assertTrue(config_status.succeeded)
#
#     def tearDown(self):
#         os.remove(os.path.join(self.workingdir, MENDEL_TEST_FILE))
#
#
#     def do_deploy(self):
#         cmdline = 'mendel -f %s dev deploy' % MENDEL_TEST_FILE
#         print cmdline
#         p = Popen(cmdline, stdout=PIPE, stderr=PIPE, shell=True, cwd=self.workingdir)
#         out, err = p.communicate()
#         print out
#         print err
#
#         myservice_http_port = os.environ.get('STANTONK/FAT-CONTAINER_8080_TCP')
#         print "HTTP PORT: %s" % myservice_http_port
#         url = 'http://127.0.0.1:%s/hello' % myservice_http_port
#         print url
#
#         # give the java service a few seconds to come up
#         status_code, content = 0, ''
#         for retries in range(0, 5):
#             try:
#                 r = urllib2.urlopen(url)
#                 content = r.read()
#                 status_code = r.getcode()
#                 # r = requests.get(url)
#                 # status_code, content = r.status_code, r.content
#             except:
#                 pass
#             time.sleep(2)
#         return status_code, content


class JarIntegrationTests(TestCase):

    def setUp(self):
        print os.environ.keys()
        curdir = os.path.dirname(os.path.abspath(__file__))

        self.workingdir = os.path.join(curdir, '..', '..', 'examples', 'java', 'jar')
        fileloc = os.path.join(self.workingdir, MENDEL_TEST_FILE)
        self.ssh_port = os.environ.get('STANTONK/FAT-CONTAINER_22_TCP')
        print "SSH PORT: %s" % self.ssh_port
        with open(fileloc, 'wb') as f:
            filecontents = MENDEL_JAR_YAML % self.ssh_port
            print filecontents
            f.write(filecontents)

    def test_jar_mendel_deploy(self):
        (status_code, content) = self.do_deploy()
        print "status code: %s" % status_code
        print "content: %s" % content
        self.assertEqual(200, status_code)
        self.assertIn('Hello', content)

    # def test_upstart_config_changes(self):
    #     state.env.user = 'vagrant'
    #     state.env.password = 'vagrant'
    #     state.env.host_string = 'localhost:%s' % self.ssh_port
    #     self.do_deploy()
    #     pre_config_status = operations.run("ps aux | grep myservice | grep changed_config | grep -v grep", warn_only=True)
    #     self.assertTrue(pre_config_status.failed) # grep returns nonzero if it doesn't find the string
    #     operations.sudo("sed -i 's/-jar/-Dchanged_config_line=true -jar/;' /etc/init/myservice.conf")
    #     self.do_deploy()
    #     config_status = operations.run("ps aux | grep myservice | grep changed_config | grep -v grep")
    #     self.assertTrue(config_status.succeeded)
    #
    def tearDown(self):
        os.remove(os.path.join(self.workingdir, MENDEL_TEST_FILE))


    def do_deploy(self):
        cmdline = 'mendel -f %s dev deploy' % MENDEL_TEST_FILE
        print cmdline
        p = Popen(cmdline, stdout=PIPE, stderr=PIPE, shell=True, cwd=self.workingdir)
        out, err = p.communicate()
        print "-------------------------------OUTPUT------------------------------------------"
        print out
        print "-------------------------------ERROR------------------------------------------"
        print err

        myservice_http_port = os.environ.get('STANTONK/FAT-CONTAINER_8080_TCP')
        print "HTTP PORT: %s" % myservice_http_port
        url = 'http://127.0.0.1:%s/hello' % myservice_http_port
        print url

        # give the java service a few seconds to come up
        status_code, content = 0, ''
        print "STATUS CODE BEFORE SERVICE STARTS UP: %s" % status_code
        for retries in range(0, 5):
            try:
                r = urllib2.urlopen(url)
                print "curling result: %s" % r
                content = r.read()
                print "My content is %s" % content
                status_code = r.getcode()
                print "status code: %s" % status_code
                # r = requests.get(url)
                # status_code, content = r.status_code, r.content
            except Exception as e:
                print "Exception raised %s %r" % (e, e)
            time.sleep(2)

        return status_code, content

