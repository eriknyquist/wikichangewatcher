import os
import unittest

from setuptools import setup
from distutils.core import Command

from wikichangewatcher import __version__

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")
REQFILE = os.path.join(HERE, 'requirements.txt')

class RunWikiChangeWatcherTests(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        suite = unittest.TestLoader().discover("tests")
        t = unittest.TextTestRunner(verbosity = 2)
        t.run(suite)

with open(README, 'r') as f:
    long_description = f.read()

with open(REQFILE, 'r') as fh:
    dependencies = fh.readlines()

setup(
    name='wikichangewatcher',
    version=__version__,
    description=('Real-time monitoring/filtering of global Wikipedia page edits'),
    long_description=long_description,
    url='http://github.com/eriknyquist/wikichangewatcher',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='Apache 2.0',
    packages=['wikichangewatcher'],
    cmdclass={'test': RunWikiChangeWatcherTests},
    entry_points={
        'console_scripts': [
            'wikiwatch=wikichangewatcher.cli:main'
        ]
    },
    install_requires=dependencies,
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
