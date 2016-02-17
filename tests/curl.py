#!/usr/bin/python

import urllib2
import json
import os


def request ( path ) :
    base_url = "http://localhost:3333/api/v1/roles"
    url = os.path.join( base_url , path )
    response = urllib2.urlopen( url )
    assert response.code == 200
    assert response.headers.type == 'application/json'
    return json.load( response )


response = request( '?name=fever' )

response = request( '10/versions/' )


response = request( '?owner__username=Feverup&name=augeas' )

response = request( '7595/versions/' )

