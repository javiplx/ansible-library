
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
import glob

class library ( flask.Flask ) :

    def __init__ ( self ) :
        flask.Flask.__init__( self , 'ansible-library' )
        self.roles_dir = None
        self.roles = []
        self.ttl = 3600
        self.galaxy = []

    conffile = "/etc/ansible-library.yml"
    appconfig = { 'roles_dir':"/var/lib/galaxy",
                  'host':"0.0.0.0",
                  'port':3333,
                  'debug':False
                  }

    def run ( self , *args, **kwargs ) :
        if os.path.isfile( self.conffile ) :
            localconf = yaml.load( open( self.conffile ) )
            self.appconfig.update( localconf )
        self.load_roles()
        flask.Flask.run( self , host=self.appconfig['host'],
                                port=self.appconfig['port'],
                                debug=self.appconfig['debug']
                                )

    def load_roles ( self ) :
        _roles = []
        for file_path in glob.glob( os.path.join( self.appconfig['roles_dir'] , "*/*.tar.gz" ) ) :
            root , file_name = os.path.split( file_path )
            tar = tarfile.open(file_path)
            meta = filter( lambda s : s.endswith('meta/main.yml') ,tar.getnames())
            if len(meta) != 1:
                print "WARNING: '%s' is not an ansible role" % file_path
                continue
            _role = yaml.load(tar.extractfile(meta[0]))
            _role.update( _role.pop('galaxy_info') )
            _role['name'] = os.path.basename(root)
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
            self.roles.append( ( -1 , _role ) )
            _role['summary_fields'] = { 'dependencies': _role.pop('dependencies'),
                                        'versions': _role.pop('versions')
                                        }
            _id += 1


