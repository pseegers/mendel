import sys

import docker

from mendel.util.colors import blue


def is_running_tests():
    """
    Apply heuristics against the list of arguments of whatever __main__
    is, so we can avoid quitting due to a lack of mendel.yml when
    the unittests are being run.
    :return: bool
    """
    test_heuristics = ['python -m unittest', 'setup.py', 'utrunner.py', 'PyCharm.app']

    running_tests = False
    for arg in sys.argv:
        if any(test_heuristic in arg for test_heuristic in test_heuristics):
            running_tests = True
            break
    return running_tests


def get_docker_attr(image='sonatype/nexus:oss', attr='ip'):
    print(blue('Extracting docker attr'))
    client = docker.from_env()
    container_list = client.containers.list()

    if len(container_list) > 0:
        for container in container_list:
            container = container.__dict__
            if container['attrs']['Config']['Image'] == image:
                if attr == 'ip':
                    ip = container['attrs']['NetworkSettings']['IPAddress']
                    return ip
                elif attr == 'hostname':
                    hostname = container['attrs']['Config']['Hostname']
                    return hostname
    else:
        raise Exception('No containers have been spun up')
