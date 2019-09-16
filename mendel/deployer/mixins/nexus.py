import os
import re
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import fromstring


class NexusMixin(object):
    """
    Common behavior for deployments that use nexus to find, download, and upload jars and packages
    """

    def _generate_base_nexus_url(self, elem_tree: ElementTree):
        """
        Generate base url for where nexus releases live
        :param elem_tree: ElementTree of the pom
        :return: str base url
        """
        nexus_url = self.config.nexus_repository
        group_id = elem_tree.findtext("{http://maven.apache.org/POM/4.0.0}groupId")

        group_id = re.sub(r'\.', '/', group_id)

        nexus_url += group_id
        nexus_url += '/'
        nexus_url += self.config.jar_name

        if not nexus_url.startswith("http"):
            nexus_url = "http://" + nexus_url
        return nexus_url

    def _generate_nexus_url(self, connection):
        """
        Generate nexus URL for artifact download
        :param: connection: Connection
        :return: str url
        As a side effect, it sets the project version on the Deployer instance
        This side effect should be pulled out and be more explicit in the future so it's less spaghetti
        """
        elem_tree = ElementTree(file=os.path.join(self.config.cwd, "pom.xml"))

        if not self.project_version:
            found = elem_tree.findtext("{http://maven.apache.org/POM/4.0.0}version")
            self.project_version = found.rstrip()
            print(f"Setting project version to to be {self.project_version}")
        elif self.project_version == 'nexus.latest':
            # slightly dirty to reuse same var, revisit later
            self.project_version = self._find_latest_nexus_version(connection)
            print(f"Setting project version to to be {self.project_version}")

        nexus_url = self._generate_base_nexus_url(elem_tree)

        nexus_url += '/'
        nexus_url += self.project_version
        nexus_url += '/'
        nexus_url += '{0}-{1}'.format(self.config.jar_name, self.project_version)

        if self.config.classifier is not None:
            nexus_url += '-{0}'.format(self.config.classifier)

        nexus_url += '.jar'

        return nexus_url

    def _find_latest_nexus_version(self, connection):
        """
        Go to nexus and find latest version of the project
        :param connection: Connection
        :return: str latest version
        """
        print("Finding latest version from Nexus...")
        elem_tree = ElementTree(file=os.path.join(self.config.cwd, "pom.xml"))
        nexus_url = self._generate_base_nexus_url(elem_tree) + '/maven-metadata.xml'
        print(nexus_url)
        maven_meta = connection.run('curl -s ' + str(nexus_url), hide='both')
        print(maven_meta)
        maven_meta_xml = fromstring(maven_meta.stdout)
        versioning = maven_meta_xml.find("versioning")
        return versioning.findtext("latest") or versioning.findtext("release")
