#!/usr/bin/env python
import inspect
import os
import uuid

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from pip.req import parse_requirements

# place __version__ in setup.py namespace, w/o
# having to import and creating a dependency nightmare
execfile('mendel/version.py')

package_dir = \
    os.path.dirname( # script directory
        os.path.abspath(
            inspect.getfile(
                inspect.currentframe())))

reqs_file = os.path.join(package_dir, 'requirements.txt')

# stupid session thing. stealing tweepy's solution:
# https://github.com/tweepy/tweepy/commit/9b4cb9eb123be05a925c1c6deaf0141699853644
install_reqs = parse_requirements(reqs_file, session=uuid.uuid1())


setup(
    name='fabric-mendel',
    install_requires=[str(ir.req) for ir in install_reqs],
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
)
