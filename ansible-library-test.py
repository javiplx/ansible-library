
import XXX
import unittest
import json


class ansible_library_test ( unittest.TestCase ) :

    def setUp ( self ) :
        XXX.app.roles = XXX.read_roles( '/var/lib/galaxy' )
        self.app = XXX.app.test_client()

    def get ( self , url ) :
        res = self.app.get( "/api/%s" % url )
        self.assertEqual( res.status_code , 200 )
        self.assertEqual( res.content_type , "application/json" )
        return json.loads(res.data)

    def test_api_version ( self ) :
        data = self.get("")
        self.assertEqual( data['current_version'] , 'v1' )

        galaxy = self.app.get( "https://galaxy.ansible.com/api/" )
        galaxy = json.loads(galaxy.data)
        self.assertEqual( data['current_version'] , galaxy['current_version'] )

    def test_local_role ( self ) :
        data = self.get( "v1/roles/?name=fever" )
        self.assertEqual( data['count'] , 1 )
        result = data['results'][0]
        self.assertEqual( result['name'] , "fever" )

    def test_local_versions ( self ) :
        data = self.get( "v1/roles/?name=fever" )
        data = self.get( "v1/roles/%s/versions/" % data['results'][0]['id'] )
        self.assertEqual( data['count'] , 2 )
        versions = map( lambda v : v['name'] , data['results'] )
        self.assertIn( "v1.0" , versions )
        self.assertIn( "v1.1" , versions )
        v11 = filter( lambda v : v['name'] == "v1.1" , data['results'] )[0]
        self.assertEqual( v11['url'] , "http://localhost/fever/v1.1.tar.gz" )

    def test_proxied_role ( self ) :
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
        data = self.get( "v1/roles/?owner__username=Feverup&name=augeas" )
        data = self.get( "v1/roles/%s/versions/" % data['results'][0]['id'] )

        galaxy = self.app.get( "https://galaxy.ansible.com/api/v1/roles/" , query_string="?owner__username=Feverup&name=augeas" )
        galaxy = json.loads(galaxy.data)
        galaxy = self.app.get( "https://galaxy.ansible.com%s" % galaxy['results'][0]['related']['versions'] )
        galaxy = json.loads(galaxy.data)
        self.assertListEqual( data['results'] , galaxy['results'] )

if __name__ == '__main__':
    unittest.main()

