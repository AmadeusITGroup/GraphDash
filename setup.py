#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Packaging
"""

from __future__ import with_statement
from setuptools import setup, find_packages

with open('VERSION') as f:
    VERSION = f.read().rstrip()

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()


setup(
    name='GraphDash',
    version=VERSION,
    author='Alex Prengère',
    author_email='alexprengere@amadeus.com',
    url='https://github.com/AmadeusITGroup/graphdash',
    description='A dashboard for graphs.',
    long_description=LONG_DESCRIPTION,
    py_modules=[
        'graphdashmain',
    ],
    packages=find_packages(),
    package_data={
        'graphdash': [
            'templates/*.html',
            'assets/css/*',
            'assets/js/*',
            'assets/img/*',
        ],
    },
    install_requires=[
        'argparse',
        'PyYAML==3.11',
        'Flask==0.11.1',
        'Markdown==2.4',
        'Pygments==2.1.3',
        'stop-words',
        'ushlex==0.99',
    ],
    entry_points={
        'console_scripts': [
            'GraphDash=graphdash.__main__:main',
        ],
    },
    scripts=[
        'GraphDashManage',
    ],
)
