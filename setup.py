#!/usr/bin/env python2.7

from __future__ import print_function

from setuptools import setup
from pip.req import parse_requirements
from pip.download import PipSession
import os
import sys
import re
import subprocess

install_reqs = parse_requirements('requirements.pip',
                                  session=PipSession())
install_requires = [str(ir.req) for ir in install_reqs if ir.req]

packages = []

for root, dirs, files in os.walk('moment_display'):
    if '__init__.py' in files:
        packages.append(re.sub('%[%A-z0-9_]+', '', root.replace('/', '.')))

is_build = len(sys.argv) > 1 and sys.argv[1] in ['sdist', 'bdist']


def get_version():
    # Skip VERSION.txt if building a package.
    if not is_build and os.path.exists("VERSION.txt"):
        with open("VERSION.txt") as ver_file:
            return ver_file.read()
    else:
        # Build version from latest tag.
        gitcommit = subprocess.check_output(
            "git rev-parse HEAD", shell=True).decode().strip()
        gitcommit.rstrip()
        gitdescribe = subprocess.check_output(
            "git describe --tags", shell=True).decode().strip()
        gitdescribe.rstrip()

        tagsearch = re.search('(.*)-(\d*)-(.*)', gitdescribe)
        if tagsearch:
            return "{}-c{}-{}".format(
                tagsearch.group(1), tagsearch.group(2), gitcommit[0:8])
        else:
            return "{}-{}".format(gitdescribe, gitcommit[0:8])

version = get_version()

# Write out VERSION.txt if building a package.
if is_build:
    with open("VERSION.txt", "w") as ver_txt:
        print("Saving version: {}".format(version))
        ver_txt.write(version)

setup(name="MomentDisplay",
      version=version,
      url="http://momently.io",
      description="Momently display app",
      author="Momently.io",
      author_email="noreply@momently.io",
      include_package_data=True,
      packages=packages,
      entry_points={
          'console_scripts': ['moment-display=moment_display.cli:display_main']
      },
      install_requires=install_requires)
