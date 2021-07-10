#!/usr/bin/env python

from setuptools import setup

setup(name='ifn-transport',
      version='0.0.1.dev0',
      description='Simple Transport Model based on Ideal Flow Network',
      long_description='{0:s}\n{1:s}'.format(
          open('README.rst').read(),
          open('CHANGES.rst').read()),
      author='Kardi Teknomo',
      author_email='kardi.teknomo@petra.ac.id',
      url='https://github.com/teknomo/ifn-transport',
      packages=['main','guiTable', 'IdealFlowNetwork', 'ifnTransport','osm2ifn','scenario'],
      zip_safe=True,
      package_dir={'ifn-transport': 'src'},
      test_suite='ifn-transport.tests',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
          'Programming Language :: Python :: 3.8',
          ],
      )