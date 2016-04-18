#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='wig',
      version='1.0',
      description='WebApp Information Gatherer',
      author='jekyc',
      #author_email='none@none.com',
      url='https://github.com/jekyc/wig',
      packages=find_packages(),
      data_files = { 'data': ['data/*']},
      data_files=[('data', ['wig/data/*'])],
     )

