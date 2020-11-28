#!/usr/bin/env python3

from setuptools import setup, find_packages
import studip_sync

setup(
    name='studip-sync',
    description='Synchronize files and media on Stud.IP',
    long_description=studip_sync.__doc__,
    version=studip_sync.__version__,
    url='https://github.com/studip-sync/studip_sync',
    author=studip_sync.__author__,
    license=studip_sync.__license__,
    scripts=['scripts/studip-sync'],
    packages=find_packages("."),
    install_requires=['beautifulsoup4', 'requests', 'lxml'],
)
