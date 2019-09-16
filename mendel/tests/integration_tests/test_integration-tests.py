import getpass
import os
import pprint
import re
import time
from unittest import TestCase
from urllib.request import urlopen

from fabric.connection import Connection
from invoke import Context

from mendel.tests.util import get_docker_attr
from mendel.util.colors import blue
from mendel.util.colors import green

MENDEL_TEST_FILE = 'mendel.test.yml'


class MendelIntegrationTests(TestCase):

    @classmethod
    def setUpClass(cls):
        hostname = get_docker_attr('stantonk/fat-container:1.3', attr='hostname')
        me = getpass.getuser()
        connection = Connection(host='localhost')
        docker_exec_prefix = f'docker exec {hostname} bash -c '

        connection.local(docker_exec_prefix + f'"useradd {me}"', hide=False)
        sudo_setup = f"echo \'{me} ALL=(ALL) NOPASSWD: ALL\'"
        time.sleep(2)
        connection.local(docker_exec_prefix + f"\"{sudo_setup} >> /etc/sudoers\"", hide=False)

        ssh_key = connection.local('cat ~/.ssh/id_rsa.pub').stdout
        connection.local(docker_exec_prefix + f'"mkdir /home/{me} -m 0700"')
        connection.local(docker_exec_prefix + f'"chown {me}:{me} /home/{me}"')
        connection.local(docker_exec_prefix + f'"mkdir /home/{me}/.ssh -m 0700"')
        connection.local(docker_exec_prefix + f'"chown {me}:{me} /home/{me}/.ssh"')
        connection.local(docker_exec_prefix + f'"touch /home/{me}/.ssh/authorized_keys"')
        connection.local(docker_exec_prefix + f'"chmod 700 /home/{me}/.ssh/authorized_keys"')
        connection.local(docker_exec_prefix + f'"chown {me}:{me} /home/{me}/.ssh/authorized_keys"')
        connection.local(docker_exec_prefix + f'"echo \'{ssh_key}\' >> /home/{me}/.ssh/authorized_keys"')
        cls.ssh_port = os.environ.get('STANTONK_FAT_CONTAINER_22_TCP_PORT')
        # We dynamically ensure deployer (you) have sudo on the docker box
        print(f"SSH PORT: {cls.ssh_port}")
        os.environ['MENDEL_GRAPHITE_HOST'] = 'www.google.com'

    def test_targz_deploy(self):
        MENDEL_YAML = """service_name: myservice-tgz
bundle_type: tgz
project_type: java
hosts:
  dev:
    hostnames: localhost
    port: %s
  stage:
    hostnames: localhost
    port: 2223"""
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.workingdir = os.path.join(curdir, '..', '..', '..', 'examples', 'java', 'tgz')
        fileloc = os.path.join(self.workingdir, MENDEL_TEST_FILE)
        self._write_mendelfile(fileloc, MENDEL_YAML, self.ssh_port)
        self.service_name = "myservice-tgz"
        self.bundle_type = 'tgz'
        self.is_ubuntu_18 = False
        self._test_mendel_deploy()

    def test_jar_deploy(self):
        MENDEL_YAML = """service_name: myservice-jar
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
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.workingdir = os.path.join(curdir, '..', '..', '..', 'examples', 'java', 'jar')
        fileloc = os.path.join(self.workingdir, MENDEL_TEST_FILE)
        self._write_mendelfile(fileloc, MENDEL_YAML, self.ssh_port)
        self.service_name = "myservice-jar"
        self.bundle_type = 'jar'
        self.is_ubuntu_18 = False
        self._test_mendel_deploy()

    def test_upstart_config_changes(self):
        MENDEL_YAML = """service_name: myservice-jar
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
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.workingdir = os.path.join(curdir, '..', '..', '..', 'examples', 'java', 'jar')
        fileloc = os.path.join(self.workingdir, MENDEL_TEST_FILE)
        self._write_mendelfile(fileloc, MENDEL_YAML, self.ssh_port)
        self.service_name = "myservice-jar"
        self.bundle_type = 'jar'
        self.is_ubuntu_18 = False
        connection = Connection(user=getpass.getuser(), host='localhost', port=self.ssh_port)
        self._do_deploy()
        pre_config_status = connection.run(
            f"ps aux | grep {self.service_name} | grep changed_config | grep -v grep",
            warn=True)
        self.assertFalse(pre_config_status.ok)  # grep returns nonzero if it doesn't find the string
        # Emulate chef change to upstart config
        connection.sudo(
            f"sed -i 's/java -jar/java -Dchanged_config_line=true -jar/;' /etc/init/{self.service_name}.conf",
            warn=True)

        self._do_deploy()
        config_status = connection.run(
            f"ps aux | grep {self.service_name} | grep changed_config | grep -v grep", warn=True)
        self.assertTrue(config_status.ok)

    def _test_mendel_deploy(self):
        status_code, content = self._do_deploy()
        print(f"status code: {status_code}")
        print(f"content: {content}")
        self.assertEqual(200, status_code)
        self.assertIn('Hello', content.decode('utf-8'))

    def _write_mendelfile(self, fileloc, yml_content, ssh_port):
        with open(fileloc, 'wb') as f:
            filecontents = (yml_content % ssh_port)
            print(blue("Mendel Config:"))
            pprint.pprint(filecontents)
            f.write(filecontents.encode('utf-8'))

    """
    def test_ubuntu18_mendel_deploy(self):
        self.is_ubuntu_18 = True
        if self.bundle_type == 'remote_jar':
            (status_code, content) = self.do_deploy(host='stage')
            print('status_code: %s' % status_code)
            print('content: %s' % content)
            self.assertEqual(200, status_code)
            self.assertIn('Hello', content)
        else:
            pass

    

    def test_systemd_config_changes(self):
        self.is_ubuntu_18 = True

        if self.bundle_type == 'remote_jar':
            connection = Connection(user='kevin', host='localhost', port=2223,
                                    connect_kwargs={'passphrase': 'vagrant'})

            self.do_deploy(host='stage')
            pre_config_status = connection.run("ps aux | grep {0} | grep verbose | grep -v grep".format(self.service_name),
                                               warn=True)
            self.assertTrue(pre_config_status.failed)

            # Emulate chef change to systemd config
            connection.sudo(
                "sed -i 's/\/usr\/bin\/java -jar/\/usr\/bin\/java -verbose -jar/;' /etc/systemd/system/{0}.service".format(
                self.service_name)
            )

            # Have to reload systemd when source config changes on disk
            reload = connection.sudo("systemctl daemon-reload")
            self.assertTrue(reload.succeeded)

            self.do_deploy(host='stage')
            config_status = connection.run("ps aux | grep {0} | grep verbose | grep -v grep".format(self.service_name), warn=True)
            self.assertTrue(config_status.succeeded)
        else:
            pass
    """

    def _do_deploy(self, host='dev'):
        connection = Context()
        mendelcmd = 'mendel -f %s %s deploy' % (MENDEL_TEST_FILE, host)
        connection.run(f'cd {self.workingdir} && {mendelcmd}')

        myservice_http_port = os.environ.get('STANTONK_FAT_CONTAINER_8080_TCP_PORT') if host == 'dev' else '8081'
        print("HTTP PORT: %s" % myservice_http_port)
        url = 'http://127.0.0.1:%s/hello' % myservice_http_port
        print(url)

        # give the java service a few seconds to come up
        status_code, content = 0, ''
        for retries in range(0, 5):
            print(blue(f'Curl attempt #{retries}'))
            try:
                r = urlopen(url)
                content = r.read()
                status_code = r.getcode()
                break
                # r = requests.get(url)
                # status_code, content = r.status_code, r.content
            except Exception:
                pass
            time.sleep(2)
        return status_code, content

    def do_versioned_deploy(self):
        # TODO
        pass

    def _update_project_version(self, pom, old_version, new_version):
        #Change the service's version because nexus does not accept same version deploys

        with open(pom, 'r') as pom_file:
            text = pom_file.read()

        os.remove(os.path.join(pom))

        with open(pom, 'wb') as new_pom_file:
            filecontents = re.sub(old_version, new_version, text)
            new_pom_file.write(filecontents)

    def tearDown(self):
        os.remove(os.path.join(self.workingdir, MENDEL_TEST_FILE))

        print(blue("User and password have been assigned"))

        if self.is_ubuntu_18 is False:
            connection = Connection(user=getpass.getuser(), host='localhost', port=self.ssh_port)
        else:
            connection = Connection(user=getpass.getuser(), host='localhost', port=2223)
            self.is_ubuntu_18 = False

        print(blue("host has been assigned. Now stopping service"))
        connection.sudo("service {0} stop".format(self.service_name), warn=True)
        print(green("Service has been stopped."))


"""
class RemoteJarIntegrationTests(IntegrationTestMixin, TestCase):


    MENDEL_YAML = "
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
    "


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
                r = urlopen(self.nexus_url)
                content = r.read()
                status_code = r.getcode()

            except:
                pass

            if (status_code != 200):
                print("Waiting for nexus")
                time.sleep(2)

        super(RemoteJarIntegrationTests, self).setUp()

    def tearDown(self):
        os.remove(os.path.join(self.pom))
        super(RemoteJarIntegrationTests, self).tearDown()

    def test_specific_version(self):
        connection = Connection(user='vagrant', host='localhost', port=self.ssh_port,
                                connect_kwargs={'password': 'vagrant'})

        # Make versions available in nexus
        self.update_project_version('0.0.6', '0.0.9')
        call('mvn deploy', shell=True, cwd=self.workingdir)

        self.update_project_version('0.0.9', '0.0.10')
        call('mvn deploy', shell=True, cwd=self.workingdir)
        self.update_project_version('0.0.10', '0.0.11')

        # Deploy a specific version (no latest)
        self.do_deploy(version='0.0.9')
        config_status = connection.run("ls -al /srv/myservice-remote_jar/current | grep {0} | grep -v grep".format('0.0.9'))
        self.assertTrue(config_status.succeeded)

        # Deploy the latest from Nexus
        self.do_deploy(version='nexus.latest')
        config_status = connection.run("ls -al /srv/myservice-remote_jar/current | grep {0} | grep -v grep".format('0.0.10'))
        self.assertTrue(config_status.succeeded)

"""
