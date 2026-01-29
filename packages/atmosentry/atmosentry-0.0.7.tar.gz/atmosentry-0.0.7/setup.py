"""
Setup script for the atmosentry package.

Package Information:
- Name: atmosentry
- Version: 0.0.7
- Author: Richard Anslow
- License: MIT License
- Description: Atmospheric entry simulation (atmosentry)
"""

from setuptools import setup, find_packages

setup(
    name='atmosentry',
    version='0.0.7',
    author='Richard Anslow',
    author_email='r.anslow@outlook.com',
    url='https://github.com/richard17a/atmosentry',
    license='MIT License',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    description='description tbd.',
    install_requires=[
        # 'python>=3.6.0',
        # 'pandas>=0.10.0'
    ]
)
