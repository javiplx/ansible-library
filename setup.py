#!/usr/bin/python

from distutils.core import setup

setup(
    name = 'ansible-library',
    version = '0.9',
    description = 'Minimal galaxy server to host private roles',
    author = 'Javier Palacios',
    author_email = 'javiplx@gmail.com',
    license = 'GPLv2',
    url = 'https://github.com/javiplx/ansible-library',
    scripts = [ 'ansible-library.py' ],
    install_requires=[ 'Werkzeug>=0.9' , 'flask>=0.10' ]
    )

