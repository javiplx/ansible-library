
# Copyright (C) 2016 Javier Palacios
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# Version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See full
# GPLv2 for more details (http://www.gnu.org/licenses/gpl-2.0.html).

import flask
import tarfile
import yaml
import operator, itertools
import os

class app ( flask.Flask ) :

    def __init__ ( self ) :
        flask.Flask.__init__( self , 'ansible-library' )
        self.roles_dir = '/var/lib/galaxy'
        self.read_roles()
        self.galaxy = []

    def read_roles ( self ) :
        _roles = []
        for root, dirs, files in os.walk(self.roles_dir) :
            for file_name in files :
                file_path = os.path.join(root,file_name)
                tar = tarfile.open(file_path)
                meta = filter( lambda s : s.endswith('meta/main.yml') ,tar.getnames())
                if len(meta) != 1:
                    print "WARNING: '%s' is not an ansible role" % file_path
                    continue
                _role = yaml.load(tar.extractfile(meta[0]))
                _role.update( _role.pop('galaxy_info') )
                if not _role.has_key('name') :
                    _role['name'] = os.path.basename(root)
                if not _role.has_key('version') :
                    _role['version'] = file_name.rpartition('.tar')[0]
                _roles.append( _role )

        _id = 1
        self.roles = []
        _roles = sorted( _roles , key=operator.itemgetter('name') )
        for k, g in itertools.groupby(_roles, operator.itemgetter('name')):
            _role = { 'id': _id }
            _role.update( g.next() )
            _role['versions'] = [ { 'name': str(_role.pop('version')) } ]
            for r in g :
              _role['versions'].append( { 'name': str(r.pop('version')) } )
            self.roles.append( _role )
            _role['summary_fields'] = { 'dependencies': _role.pop('dependencies'),
                                        'versions': _role.pop('versions')
                                        }
            _id += 1


