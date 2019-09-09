#!/usr/bin/env python
import inspect
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


# place __version__ in setup.py namespace, w/o
# having to import and creating a dependency nightmare
execfile('mendel/version.py')

package_dir = \
    os.path.dirname( # script directory
        os.path.abspath(
            inspect.getfile(
                inspect.currentframe())))

reqs_file = os.path.join(package_dir, 'requirements.txt')

install_reqs = parse_requirements(reqs_file)


setup(
    name='fabric-mendel',
    install_requires=[str(ir) for ir in install_reqs],
    version=__version__, # comes from execfile() invocation above; IDEs will complain.
    description='Fabric Tooling for deploying services',
    author='Sprout Social, Inc.',
    url='https://github.com/sproutsocial/mendel',
    scripts=[
        'bin/mendel'
    ],
    packages=[
        'mendel'
    ],
    zip_safe=False,
    license='MIT',
    test_suite='mendel.tests',
    setup_requires=['pytest-runner', ],
    tests_require=['pytest', ],
)
