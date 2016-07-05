#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Packaging
"""

from __future__ import with_statement
import sys
from setuptools import setup, find_packages

with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()

with open('LICENSE') as f:
    LICENSE = f.read()

INSTALL_REQUIRES = [
    'argparse',
    'PyYAML==3.11',
    'Flask==0.11.1',
    'Markdown==2.4',
    'Pygments==2.1.3',
    'stop-words',
]

if sys.version_info[0] < 3:
    INSTALL_REQUIRES.append('ushlex==0.99')

setup(
    name='GraphDash',
    version='0.9.1',
    author='Alex Prengère',
    author_email='alexprengere@amadeus.com',
    url='https://github.com/AmadeusITGroup/graphdash',
    description='A web-based dashboard built on graphs and their metadata.',
    long_description=LONG_DESCRIPTION,
    license=LICENSE,
    packages=find_packages(),
    package_data={
        'graphdash': [
            'templates/*.html',
            'assets/css/*',
            'assets/js/*',
            'assets/img/*',
        ],
    },
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts': [
            'GraphDash=graphdash.__main__:main',
        ],
    },
    scripts=[
        'GraphDashManage',
    ],
)
