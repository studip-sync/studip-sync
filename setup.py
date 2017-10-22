#!/usr/bin/env python

from setuptools import setup
import studip_sync

setup(
    name='studip_sync',
    description='Synchronize files on Stud.IP',
    long_description=studip_sync.__doc__,
    version=studip_sync.__version__,
    url='https://github.com/woefe/studip_sync',
    author=studip_sync.__author__,
    author_email=studip_sync.__email__,
    license=studip_sync.__license__,
    scripts=['scripts/studip_sync'],
    packages=['studip_sync'],
    install_requires=['selenium', 'requests'],
)
