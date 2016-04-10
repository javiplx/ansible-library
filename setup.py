#!/usr/bin/python

from distutils.core import setup

setup(
    name = 'ansible-library',
    version = '1.0',
    description = 'Minimal galaxy server to host private roles',
    author = 'Javier Palacios',
    author_email = 'javiplx@gmail.com',
    license = 'GPLv2',
    url = 'https://github.com/javiplx/ansible-library',
    scripts = [ 'ansible-library.py' ],
    packages = [ 'ansible_library' ],
    install_requires=[ 'Werkzeug>=0.9' , 'flask>=0.10' , 'ansible>=1.9.2' , 'pyyaml' ]
    )

