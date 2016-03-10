
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

import ansible_library
import unittest
import json
import os
import shutil
import tempfile
import yaml
import tarfile

from ansible.module_utils.urls import open_url


class ansible_library_test ( unittest.TestCase ) :

    @classmethod
    def setUpClass ( cls ) :
        cls._tempdir = tempfile.mkdtemp()
        roles = yaml.load( open( 'tests/fixtures/roles.yml' ) )
        for role in roles :
            role_name = role.pop('name')
            if not os.path.exists( "%s/%s" % ( cls._tempdir , role_name ) ) :
                os.mkdir( "%s/%s" % ( cls._tempdir , role_name ) )
            file_name = "%s/%s.tar.gz" % ( role_name , role['galaxy_info']['version'] )
            with open( "%s/meta.yml" % cls._tempdir , 'w' ) as fd :
                yaml.dump(role, fd, default_flow_style=False)
            with tarfile.open( "%s/%s" % ( cls._tempdir , file_name ) , mode="w:gz" ) as tar :
                tar.add( "%s/meta.yml" % cls._tempdir , "%s/meta/main.yml" % role_name )
        os.unlink("%s/meta.yml" % cls._tempdir)

    @classmethod
    def tearDownClass ( cls ) :
        shutil.rmtree( cls._tempdir )

    def unpack_roles ( self ) :
        roles = yaml.load( open( 'tests/fixtures/extraroles.yml' ) )
        for role in roles :
            role_name = role.pop('name')
            if not os.path.exists( "%s/%s" % ( self._tempdir , role_name ) ) :
                os.mkdir( "%s/%s" % ( self._tempdir , role_name ) )
            file_name = "%s/%s.tar.gz" % ( role_name , role['galaxy_info']['version'] )
            with open( "%s/meta.yml" % self._tempdir , 'w' ) as fd :
                yaml.dump(role, fd, default_flow_style=False)
            with tarfile.open( "%s/%s" % ( self._tempdir , file_name ) , mode="w:gz" ) as tar :
                tar.add( "%s/meta.yml" % self._tempdir , "%s/meta/main.yml" % role_name )
        os.unlink("%s/meta.yml" % self._tempdir)

    def setUp ( self ) :
        ansible_library.app.appconfig['roles_dir'] = self._tempdir
        ansible_library.app.load_roles()
        self.app = ansible_library.app.test_client()
        self.app.testing = True

    def get ( self , url ) :
        res = self.app.get( "/api/%s" % url )
        self.assertEqual( res.status_code , 200 )
        self.assertEqual( res.content_type , "application/json" )
        return json.loads(res.data)

    def put ( self , url ) :
        res = self.app.put( "/api/%s" % url )
        self.assertEqual( res.status_code , 200 )
        self.assertEqual( res.content_type , "application/json" )
        return json.loads(res.data)

    def test_api_version ( self ) :
        '''Verify API version'''
        data = self.get("")
        self.assertEqual( data['current_version'] , 'v1' )

        galaxy = self.app.get( "https://galaxy.ansible.com/api/" )
        galaxy = json.loads(galaxy.data)
        self.assertEqual( data['current_version'] , galaxy['current_version'] )

    def test_local_role ( self ) :
        '''Get data for local role'''
        data = self.get( "v1/roles/?name=fever" )
        self.assertEqual( data['count'] , 1 )
        result = data['results'][0]
        self.assertEqual( result['name'] , "fever" )

    def test_local_versions ( self ) :
        '''Get versions of local role'''
        data = self.get( "v1/roles/?name=fever" )
        data = self.get( "v1/roles/%s/versions/" % data['results'][0]['id'] )
        self.assertEqual( data['count'] , 2 )
        versions = map( lambda v : v['name'] , data['results'] )
        self.assertIn( "v1.0" , versions )
        self.assertIn( "v1.1" , versions )
        v11 = filter( lambda v : v['name'] == "v1.1" , data['results'] )[0]
        self.assertEqual( v11['download'] , "http://localhost/fever/v1.1.tar.gz" )

    def test_download_local_role ( self ) :
        '''Download role tarball'''
        data = self.get( "v1/roles/1/versions/" )
        self.assertNotEqual( data['results'][0]['download'] , "" )
        role_tarball = self.app.get(data['results'][0]['download'])
        self.assertEqual( role_tarball.status_code , 200 )

    def test_proxied_role ( self ) :
        '''Get public galaxy role if not a local one'''
        data = self.get( "v1/roles/?owner__username=Feverup&name=augeas" )
        self.assertEqual( data['count'] , 1 )
        result = data['results'][0]
        self.assertEqual( result['namespace'] , "Feverup" )
        self.assertEqual( result['name'] , "augeas" )

        galaxy = self.app.get( "https://galaxy.ansible.com/api/v1/roles/" , query_string="?owner__username=Feverup&name=augeas" )
        galaxy = json.loads(galaxy.data)
        self.assertEqual( galaxy['count'] , 1 )
        self.assertDictEqual( data['results'][0] , galaxy['results'][0] )

    def test_proxied_versions ( self ) :
        '''Proxying versions from public galaxy'''
        data = self.get( "v1/roles/?owner__username=Feverup&name=augeas" )
        data = self.get( "v1/roles/%s/versions/" % data['results'][0]['id'] )

        galaxy = self.app.get( "https://galaxy.ansible.com/api/v1/roles/" , query_string="?owner__username=Feverup&name=augeas" )
        galaxy = json.loads(galaxy.data)
        galaxy = self.app.get( "https://galaxy.ansible.com%s" % galaxy['results'][0]['related']['versions'] )
        galaxy = json.loads(galaxy.data)
        self.assertListEqual( data['results'] , galaxy['results'] )

    def test_url_for_proxied_role ( self ) :
        '''Check url returned for proxied roles (regression javiplx/ansible-library#1)'''
        data = self.get( "v1/roles/?owner__username=Feverup&name=augeas" )
        data = self.get( "v1/roles/%s/versions/" % data['results'][0]['id'] )
        self.assertEqual( data['results'][0]['download'] , "" )

    def test_version_field_class ( self ) :
        '''Ensure that versions are returned as strings (regression javiplx/ansible-library#8)'''
        data = self.get( "v1/roles/?name=djangoserver" )
        data = self.get( "v1/roles/%s/versions/" % data['results'][0]['id'] )
        self.assertEqual( data['count'] , 2 )
        for d in data['results'] :
            self.assertIsInstance(d['name'], unicode)

    def test_roles_reload ( self ) :
        '''Reload roles from filesystem'''
        self.unpack_roles()

        data = self.put("reload")
        self.assertEqual( data['msg'] , 'Done' )

        data = self.get( "v1/roles/?name=dnsmasq" )
        self.assertEqual( data['count'] , 1 )

