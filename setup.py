#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os.path import dirname, join

from setuptools import find_packages, setup

__version__= "0.0.3"

def read_file(file):
    with open(file, "rt") as f:
        return f.read()
    

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
    install_requires=["dill>=0.3.8", "thriftpy2>=0.3.9","pandas==1.3.4"],
    zip_safe=False,    
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)