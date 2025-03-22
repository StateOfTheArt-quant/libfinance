#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os.path import dirname, join

from setuptools import find_packages, setup

__version__= "0.0.3"


install_requires = ["lz4","msgpack","pandas>=1.3.4"]

    

setup(
    name='libfinance',
    version=__version__,
    description='libfinance',
    packages=find_packages(exclude=[]),
    author='',
    author_email='',
    license='Apache License v2',
    package_data={'': ['*.*']},
    url='',
    install_requires=install_requires,
    zip_safe=False,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',    
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)