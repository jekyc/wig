#!/usr/bin/env python

from setuptools import setup, find_packages

import os

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append('../' + os.path.join(path, filename))
    return paths

extra_files = package_files('wig/data')

setup(name='wig',
      version='0.6',
      description='WebApp Information Gatherer',
      author='jekyc',
      #author_email='none@none.com',
      url='https://github.com/jekyc/wig',
      packages=find_packages(),
      package_data={'': extra_files},
     )

