
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
import glob
import logging


class abstract_role ( dict ) :

    def __init__ ( self , content={} ) :
        dict.__init__( self , content )

    def set_url ( self , roles_dir , version ) :
        version['download'] = ""

    def expired ( self ) :
        False

class role ( abstract_role ) :

    def __init__ ( self , id ) :
        abstract_role.__init__( self )
        self['id'] = id

    def set_url ( self , root_url , version ) :
        version['download'] = "%s%s/%s.tar.gz" % ( root_url , self['name'] , version['name'] )

class galaxy_role ( abstract_role ) :

    def __init__ ( self , file_path ) :
        tar = tarfile.open( file_path )
        meta = filter( lambda s : s.endswith('meta/main.yml') ,tar.getnames())
        if len(meta) != 1:
            print "WARNING: '%s' is not an ansible role" % file_path
            return
        data = yaml.load( tar.extractfile(meta[0]) )
        abstract_role.__init__( self , data['galaxy_info'] )
        self['dependencies'] = data.get('dependencies', [])
        dir_name , file_name = os.path.split( file_path )
        self['name'] = os.path.basename( dir_name )
        self['version'] = file_name.rpartition('.tar')[0]


class role_list ( list ) :

    def clear ( self ) :
        while self :
            self.pop()

    def add_roles ( self , role_list , next_id=None ) :
        if not next_id :
            next_id = self.next_id()
        _role = role( next_id )
        _role.update( role_list.next() )
        _role['versions'] = [ { 'name': str(_role.pop('version')) } ]
        for r in role_list :
            _role['versions'].append( { 'name': str(r.pop('version')) } )
        _role['summary_fields'] = { 'dependencies': _role.pop('dependencies'),
                                    'versions': _role.pop('versions')
                                    }
        self.append( _role )

    def by_name ( self , name ) :
        return filter( lambda d : d['name'] == name , self )

    def by_id ( self , id ) :
        return filter( lambda d : d['id'] == id , self )

    def next_id ( self ) :
        ids = map( lambda x : x['id'] , self )
        return 1 + max(ids)

class proxied_role ( abstract_role ) :

    def __init__ ( self , galaxy_metadata , ttl ) :
        self.expiration = time.time() + ttl
        abstract_role.__init__( self , galaxy_metadata )

    def expired ( self ) :
        time.time() > self.expiration


class library ( flask.Flask ) :

    def __init__ ( self ) :
        flask.Flask.__init__( self , 'ansible-library' )
        self.roles = role_list()
        self.galaxy = []

    conffile = "/etc/ansible-library.yml"
    appconfig = { 'roles_dir': "/var/lib/galaxy",
                  'logfile': None,
                  'listen': "0.0.0.0",
                  'port': 3333,
                  'ttl': 3600,
                  'daemonize': False,
                  'piddir': None,
                  'debug': False
                  }

    def run ( self , *args, **kwargs ) :
        if os.path.isfile( self.conffile ) :
            localconf = yaml.load( open( self.conffile ) )
            if localconf :
                self.appconfig.update( localconf )
        if self.appconfig['daemonize'] :
            if not self.appconfig['logfile'] :
                print "ERROR: daemonization requires a logfile"
                os.sys.exit(1)
            newpid = os.fork()
            if newpid :
                if self.appconfig['piddir'] :
                    pidfile = os.path.join( self.appconfig['piddir'] , 'ansible-library.pid' )
                    with open( pidfile , 'w' ) as fd :
                        fd.write( "%d\n" % newpid )
                os.sys.exit()
            else :
                os.sys.stdout = open(os.devnull, 'w')
                os.sys.stderr = open(os.devnull, 'w')
        if self.appconfig['logfile'] :
            logger = logging.getLogger('werkzeug')
            logger.addHandler( logging.FileHandler( self.appconfig['logfile'] ) )
            os.sys.stdout = open(os.devnull, 'w')
            os.sys.stderr = open(os.devnull, 'w')
        self.load_roles()
        flask.Flask.run( self , host=self.appconfig['listen'],
                                port=self.appconfig['port'],
                                debug=self.appconfig['debug']
                                )

    def load_roles ( self ) :
        _roles = []
        for file_path in glob.glob( os.path.join( self.appconfig['roles_dir'] , "*/*.tar.gz" ) ) :
            _roles.append( galaxy_role( file_path ) )

        _id = 1
        self.roles.clear()
        _roles = sorted( _roles , key=operator.itemgetter('name') )
        for k, g in itertools.groupby(_roles, operator.itemgetter('name')):
            self.roles.add_roles( g , _id )
            _id += 1


