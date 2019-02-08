import docker
import os
import urllib2
import time
import re
from fabric import state
from fabric import operations
from subprocess import PIPE, Popen, call
from unittest import TestCase

from fabric.colors import blue, green
from fabric.context_managers import lcd

MENDEL_TEST_FILE = 'mendel.test.yml'

class IntegrationTestMixin(object):

    def setUp(self):
        print os.environ.keys()
        self.ssh_port = os.environ.get('STANTONK/FAT-CONTAINER_22_TCP')
        print "SSH PORT: %s" % self.ssh_port
        with open(self.fileloc, 'wb') as f:
            filecontents = self.MENDEL_YAML % self.ssh_port
            print filecontents
            f.write(filecontents)

        os.environ['MENDEL_GRAPHITE_HOST'] = 'www.google.com'
        super(IntegrationTestMixin, self).setUp()

    def test_mendel_deploy(self):
        (status_code, content) = self.do_deploy()
        print "status code: %s" % status_code
        print "content: %s" % content
        self.assertEqual(200, status_code)
        self.assertIn('Hello', content)

    def test_ubuntu18_mendel_deploy(self):
        self.is_ubuntu_18 = True
        if self.bundle_type == 'remote_jar':
            (status_code, content) = self.do_deploy(host='stage')
            print 'status_code: %s' % status_code
            print 'content: %s' % content
            self.assertEqual(200, status_code)
            self.assertIn('Hello', content)
        else:
            pass

    def test_upstart_config_changes(self):
        state.env.user = 'vagrant'
        state.env.password = 'vagrant'
        state.env.host_string = 'localhost:%s' % self.ssh_port

        self.do_deploy()
        pre_config_status = operations.run("ps aux | grep {0} | grep changed_config | grep -v grep".format(self.service_name),
                                           warn_only=True)
        self.assertTrue(pre_config_status.failed)  # grep returns nonzero if it doesn't find the string
        # Emulate chef change to upstart config
        operations.sudo("sed -i 's/java -jar/java -Dchanged_config_line=true -jar/;' /etc/init/{0}.conf".format(self.service_name), warn_only=True)

        self.do_deploy()
        config_status = operations.run("ps aux | grep {0} | grep changed_config | grep -v grep".format(self.service_name), warn_only=True)
        self.assertTrue(config_status.succeeded)

    def test_systemd_config_changes(self):
        self.is_ubuntu_18 = True

        if self.bundle_type == 'remote_jar':
            state.env.user = 'vagrant'
            state.env.password = 'vagrant'
            state.env.host_string = 'localhost:2223'

            self.do_deploy(host='stage')
            pre_config_status = operations.run("ps aux | grep {0} | grep verbose | grep -v grep".format(self.service_name),
                                               warn_only=True)
            self.assertTrue(pre_config_status.failed)

            # Emulate chef change to systemd config
            operations.sudo(
                "sed -i 's/\/usr\/bin\/java -jar/\/usr\/bin\/java -verbose -jar/;' /etc/systemd/system/{0}.service".format(
                self.service_name)
            )

            # Have to reload systemd when source config changes on disk
            reload = operations.sudo("systemctl daemon-reload")
            self.assertTrue(reload.succeeded)

            self.do_deploy(host='stage')
            config_status = operations.run("ps aux | grep {0} | grep verbose | grep -v grep".format(self.service_name), warn_only=True)
            self.assertTrue(config_status.succeeded)
        else:
            pass

    def do_deploy(self, version=None, host='dev'):
        if version:
            cmdline = 'mendel -f %s %s deploy:%s' % (MENDEL_TEST_FILE, host, version)
        else:
            cmdline = 'mendel -f %s %s deploy' % (MENDEL_TEST_FILE, host)

        print state.env
        print cmdline

        # This call stalls with ubuntu 18.04 based container, not sure why so hacking around it
        # when testing ubuntu 18
        if not self.is_ubuntu_18:
            p = Popen(cmdline, stdout=PIPE, stderr=PIPE, shell=True, cwd=self.workingdir)
            out, err = p.communicate()
            print out
            print err
        else:
            with lcd(self.workingdir):
                operations.local(cmdline, capture=False)

        myservice_http_port = os.environ.get('STANTONK/FAT-CONTAINER_8080_TCP') if host=='dev' else '8081'
        print "HTTP PORT: %s" % myservice_http_port
        url = 'http://127.0.0.1:%s/hello' % myservice_http_port
        print url

        # give the java service a few seconds to come up
        status_code, content = 0, ''
        for retries in range(0, 5):
            print blue('Curl attempt #%d' % retries)
            try:
                r = urllib2.urlopen(url)
                content = r.read()
                status_code = r.getcode()
                # r = requests.get(url)
                # status_code, content = r.status_code, r.content
            except Exception:
                pass
            time.sleep(2)
        return status_code, content

    def update_project_version(self, old_version, new_version):
        """Change the service's version because nexus does not accept same version deploys"""

        with open(self.pom, 'r') as pom_file:
            text = pom_file.read()

        os.remove(os.path.join(self.pom))

        with open(self.pom, 'wb') as new_pom_file:
            filecontents = re.sub(old_version, new_version, text)
            new_pom_file.write(filecontents)

    def tearDown(self):
        os.remove(os.path.join(self.workingdir, MENDEL_TEST_FILE))
        state.env.user = 'vagrant'
        state.env.password = 'vagrant'
        print blue("User and password have been assigned")

        if self.is_ubuntu_18 is False:
            state.env.host_string = 'localhost:%s' % self.ssh_port
        else:
            state.env.host_string = 'localhost:2223'
            self.is_ubuntu_18 = False

        print blue("host has been assigned. Now stopping service")
        operations.sudo("service {0} stop".format(self.service_name), warn_only=True)
        print green("Service has been stopped.")

        super(IntegrationTestMixin, self).tearDown()


class TgzIntegrationTests(IntegrationTestMixin, TestCase):

    MENDEL_YAML = """
    service_name: myservice-tgz
    bundle_type: tgz
    project_type: java
    hosts:
      dev:
        hostnames: 127.0.0.1
        port: %s
      stage:
        hostnames: 127.0.0.1
        port: 2223
    """

    def setUp(self):
        self.curdir = os.path.dirname(os.path.abspath(__file__))
        self.workingdir = os.path.join(self.curdir, '..', '..', 'examples', 'java', 'tgz')
        self.fileloc = os.path.join(self.workingdir, MENDEL_TEST_FILE)
        self.service_name = "myservice-tgz"
        self.bundle_type = 'tgz'
        self.is_ubuntu_18 = False

        super(TgzIntegrationTests, self).setUp()


class JarIntegrationTests(IntegrationTestMixin, TestCase):

    MENDEL_YAML = """
    service_name: myservice-jar
    bundle_type: jar
    project_type: java
    build_target_path: target/
    hosts:
      dev:
        hostnames: 127.0.0.1
        port: %s
      stage:
        hostnames: 127.0.0.1
        port: 2223
    """

    def setUp(self):
        self.curdir = os.path.dirname(os.path.abspath(__file__))
        self.workingdir = os.path.join(self.curdir, '..', '..', 'examples', 'java', 'jar')
        self.fileloc = os.path.join(self.workingdir, MENDEL_TEST_FILE)
        self.service_name = "myservice-jar"
        self.bundle_type = 'jar'
        self.is_ubuntu_18 = False

        super(JarIntegrationTests, self).setUp()


class RemoteJarIntegrationTests(IntegrationTestMixin, TestCase):


    MENDEL_YAML = """
    service_name: myservice-remote_jar
    bundle_type: remote_jar
    project_type: java
    build_target_path: target/
    hosts:
      dev:
        hostnames: 127.0.0.1
        port: %s
      stage:
        hostnames: 127.0.0.1
        port: 2223
    """


    def setUp(self):
        nexus_hostname = self.get_nexus_hostname()
        self.bundle_type = 'remote_jar'
        self.curdir = os.path.dirname(os.path.abspath(__file__))
        self.workingdir = os.path.join(self.curdir, '..', '..', 'examples', 'java', 'remote_jar', 'myservice')
        self.fileloc = os.path.join(self.workingdir, MENDEL_TEST_FILE)
        self.service_name = "myservice-remote_jar"
        self.pom_template = os.path.join(self.workingdir, 'tmp.xml')
        self.pom = os.path.join(self.workingdir, 'pom.xml')
        self.old_url = 'http://localhost:8081/nexus/content/repositories/releases/'
        self.is_ubuntu_18 = False

        nexus_port = os.environ.get('SONATYPE/NEXUS_8081_TCP')
        self.nexus_url = 'http://localhost:%s/nexus/content/repositories/releases/' % nexus_port
        self.curl_url = '{0}:{1}/nexus/content/repositories/releases/'.format(nexus_hostname, '8081')
        os.environ['MENDEL_NEXUS_REPOSITORY'] = self.curl_url

        with open(self.pom_template, 'r') as tmp_file:
            text = tmp_file.read()

        with open(self.pom, 'wb') as pom_file:
            filecontents = re.sub(self.old_url, self.nexus_url, text)
            pom_file.write(filecontents)

        # Wait for nexus to come up
        status_code = False
        for retries in range(0, 10):
            try:
                r = urllib2.urlopen(self.nexus_url)
                content = r.read()
                status_code = r.getcode()

            except:
                pass

            if (status_code != 200):
                print "Waiting for nexus"
                time.sleep(2)

        super(RemoteJarIntegrationTests, self).setUp()

    def tearDown(self):
        os.remove(os.path.join(self.pom))
        super(RemoteJarIntegrationTests, self).tearDown()

    def test_specific_version(self):
        state.env.user = 'vagrant'
        state.env.password = 'vagrant'
        state.env.host_string = 'localhost:%s' % self.ssh_port

        # Make versions available in nexus
        self.update_project_version('0.0.6', '0.0.9')
        call('mvn deploy', shell=True, cwd=self.workingdir)

        self.update_project_version('0.0.9', '0.0.10')
        call('mvn deploy', shell=True, cwd=self.workingdir)
        self.update_project_version('0.0.10', '0.0.11')

        # Deploy a specific version (no latest)
        self.do_deploy(version='0.0.9')
        config_status = operations.run("ls -al /srv/myservice-remote_jar/current | grep {0} | grep -v grep".format('0.0.9'))
        self.assertTrue(config_status.succeeded)

        # Deploy the latest from Nexus
        self.do_deploy(version='nexus.latest')
        config_status = operations.run("ls -al /srv/myservice-remote_jar/current | grep {0} | grep -v grep".format('0.0.10'))
        self.assertTrue(config_status.succeeded)


    @staticmethod
    def get_nexus_hostname():
        print blue('Extracting nexus hostname...')
        client = docker.from_env()
        container_list = client.containers.list()

        if len(container_list) > 0:
            for container in container_list:
                container = container.__dict__
                if container['attrs']['Config']['Image'] == 'sonatype/nexus:oss':
                    hostname = container['attrs']['NetworkSettings']['IPAddress']
                    return hostname
        else:
            raise Exception('No containers have been spun up')