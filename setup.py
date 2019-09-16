#!/usr/bin/env python
import inspect
import os

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


# place __version__ in setup.py namespace, w/o
# having to import and creating a dependency nightmare
exec(open("mendel/version.py").read())
_locals = {}
with open("mendel/version.py") as fp:
    exec(fp.read(), None, _locals)
version = _locals["__version__"]

package_dir = \
    os.path.dirname(  # script directory
        os.path.abspath(
            inspect.getfile(
                inspect.currentframe())))

reqs_file = os.path.join(package_dir, 'requirements.txt')

install_reqs = parse_requirements(reqs_file)

package_name = "mendel"
binary_name = "mendel"
packages = find_packages(
    include=[package_name, "{}.*".format(package_name)]
)

setup(
    name='fabric-mendel',
    install_requires=[str(ir) for ir in install_reqs],
    packages=packages,
    version=version,
    description='Fabric Tooling for deploying services',
    author='Sprout Social, Inc.',
    url='https://github.com/sproutsocial/mendel',
    scripts=[
        'bin/mendel'
    ],
    zip_safe=False,
    license='MIT',
    test_suite='mendel',
    setup_requires=['pytest-runner', ],
    tests_require=['pytest', ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries",
    ],
)
