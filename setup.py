#!/usr/bin/env python

from distutils.core import setup

setup(name='Micropress',
      version='0.1',
      description='Static site generator',
      author='Joel Carranza',
      author_email='joel.carranza@gmail.com',
      url='http://carranza-collective.com/joel/',
      packages=['micropress', 'micropress.data'],
      scripts=['scripts/micropress']
     )