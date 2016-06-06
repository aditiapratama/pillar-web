#!/usr/bin/env python

"""Setup file for testing, not for packaging/distribution."""

import setuptools

setuptools.setup(
    name='pillar-web',
    version='1.0',
    packages=setuptools.find_packages('pillar-web', exclude=['manage']),
    package_dir={'': 'pillar-web'},
    tests_require=['pytest'],
    zip_safe=False,
)
