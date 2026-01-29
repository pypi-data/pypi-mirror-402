import glob
import os
import re
import shutil
from distutils.dir_util import copy_tree
from setuptools import setup
from setuptools.command.build_py import build_py

TOP_LEVEL_PACKAGE_NAME = "lcdp_api"
REST_PACKAGE_NAME = "rest"
REST_PACKAGE = ".".join([TOP_LEVEL_PACKAGE_NAME, REST_PACKAGE_NAME])
EVENT_PACKAGE_NAME = "event"
EVENT_PACKAGE = ".".join([TOP_LEVEL_PACKAGE_NAME, EVENT_PACKAGE_NAME])

class CustomBuild(build_py):
  def run(self):
    # Run classic build that will convert ghost_package to toplevel
    build_py.run(self)

    # Find toplevel and add files in it
    rest_package = os.path.join(self.build_lib, TOP_LEVEL_PACKAGE_NAME, REST_PACKAGE_NAME)
    event_package = os.path.join(self.build_lib, TOP_LEVEL_PACKAGE_NAME, EVENT_PACKAGE_NAME)
    copy_tree("rest", rest_package)
    copy_tree("event", event_package)

setup(
  name="lcdp_api",
  version_config={
    "dirty_template": "{tag}.post{ccount}+git.{sha}", # See : https://github.com/dolfinus/setuptools-git-versioning/pull/16#issuecomment-867444549
  },
  setup_requires=['setuptools-git-versioning==1.4.0'],
  packages=[TOP_LEVEL_PACKAGE_NAME,
            REST_PACKAGE,
            EVENT_PACKAGE,
            ],
  package_data={
    # If any package contains files, include them:
    REST_PACKAGE: ['*.yaml'],
    EVENT_PACKAGE: ['*/*.avsc'],
  },
  package_dir={TOP_LEVEL_PACKAGE_NAME: 'ghost_package'},
  license='Apache-2.0',
  description='Rest api specification for Le Comptoir Des Pharmacies',
  long_description='Rest api specification for Le Comptoir Des Pharmacies',
  author='Le Comptoir Des Pharmacies',
  author_email='g.thrasibule@lecomptoirdespharmacies.fr',
  url='https://bitbucket.org/lecomptoirdespharmacies/lcdp-api',
  keywords=['openapi', 'rest-api', 'rest', 'openapi3'],
  cmdclass={'build_py': CustomBuild},
)
