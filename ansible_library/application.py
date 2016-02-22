
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
import time
import os


class role ( dict ) :

    def __init__ ( self , id ) :
        dict.__init__( self )
        self['id'] = id

class galaxy_role ( dict ) :

    def __init__ ( self , dir_name , file_name ) :
        dict.__init__( self )
        tar = tarfile.open( os.path.join( dir_name , file_name ) )
        meta = filter( lambda s : s.endswith('meta/main.yml') ,tar.getnames())
        if len(meta) != 1:
            print "WARNING: '%s' is not an ansible role" % os.path.join( dir_name , file_name )
            return
        data = yaml.load( tar.extractfile(meta[0]) )
        self.update( data['galaxy_info'] )
        self['dependencies'] = data['dependencies']
        self.set_name( os.path.basename(dir_name) )
        self.set_version( file_name.rpartition('.tar')[0] )

    def set_name ( self , name ) :
        if not self.has_key('name') :
            self['name'] = name

    def set_version ( self , version ) :
        if not self.has_key('version') :
            self['version'] = version


class proxied_role ( dict ) :

    def __init__ ( self , galaxy_metadata ) :
        self.tstamp = time.time()
        dict.__init__( self , galaxy_metadata )


class library ( flask.Flask ) :

    def __init__ ( self ) :
        flask.Flask.__init__( self , 'ansible-library' )
        self.roles_dir = None
        self.roles = []
        self.ttl = 3600
        self.galaxy = []

    def run ( self , *args, **kwargs ) :
        if self.roles_dir :
            self.load_roles()
        flask.Flask.run( self , *args, **kwargs )

    def load_roles ( self ) :
        _roles = []
        for root, dirs, files in os.walk(self.roles_dir) :
            for file_name in files :
               _roles.append( galaxy_role( root , file_name ) )

        _id = 1
        self.roles = []
        _roles = sorted( _roles , key=operator.itemgetter('name') )
        for k, g in itertools.groupby(_roles, operator.itemgetter('name')):
            _role = role( _id )
            _role.update( g.next() )
            _role['versions'] = [ { 'name': str(_role.pop('version')) } ]
            for r in g :
              _role['versions'].append( { 'name': str(r.pop('version')) } )
            self.roles.append( _role )
            _role['summary_fields'] = { 'dependencies': _role.pop('dependencies'),
                                        'versions': _role.pop('versions')
                                        }
            _id += 1


