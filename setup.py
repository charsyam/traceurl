#!/usr/bin/env python

from setuptools import setup

setup(name='traceurl',
        version='0.9.13',
        description='Python Url Tracing Library',
        author='DaeMyung Kang',
        author_email='charsyam@gmail.com',
        url='https://github.com/charsyam/traceurl',
        platforms='any',
        install_requires=['httplib2'],
        packages=['traceurl'],
        scripts=['traceurl/__init__.py']
        )
