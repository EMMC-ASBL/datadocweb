# -*- coding: utf-8 -*-
"""
    Setup/install datadoc Python package
"""

from setuptools import setup, find_packages

setup(
    name='datadoc',
    version='24.10',
    packages=find_packages(),
    install_requires=['numpy', 'requests']
)
