
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

import application
import flask
import os

from ansible.module_utils.urls import open_url

me = { "description": "ansible-library REST API",
       "current_version": "v1",
       "available_versions": {"v1": "/api/v1/"}
       }

app = application.library()

@app.route("/monitor/")
def monitor():
    return flask.jsonify({'msg': 'Running'}) , 200

@app.route("/api/")
def api():
    return flask.jsonify(me)

@app.route('/api/reload', methods=['PUT'])
def reload():
    flask.current_app.load_roles()
    return flask.jsonify({'msg': 'Done'})

@app.before_request
def before_request():
    for role in flask.current_app.roles :
        if role.expired() :
            flask.current_app.roles.remove( role )

@app.route("/api/v1/roles/")
def get_roles():
    user = flask.request.args.get('owner__username')
    name = flask.request.args.get('name')
    roles = flask.current_app.roles.by_name( name )
    if not roles :
        galaxy_url = "https://galaxy.ansible.com%s" % flask.request.full_path
        response = flask.json.load(open_url(galaxy_url))
        results = map( lambda x : application.proxied_role(x, flask.current_app.appconfig['ttl']) , response['results'] )
        flask.current_app.roles.extend( results )
        return flask.jsonify(response)
    resp = { "count": len(roles),
             "cur_page": len(roles),
             "num_pages": len(roles),
             "next": None,
             "previous": None,
             "results": roles
             }
    return flask.jsonify(resp)

@app.route("/api/v1/roles/<int:id>/versions/")
def get_versions(id):
    role = flask.current_app.roles.by_id( id )
    if len(role) == 0 :
        galaxy_url = "https://galaxy.ansible.com%s" % flask.request.full_path
        return open_url(galaxy_url).read()
    versions = role[0]['summary_fields']['versions']
    role_info = { 'summary_fields': { "role": { "id": role[0]['id'] , "name": role[0]['name'] } } }
    map( lambda d : role[0].set_url( flask.request.url_root , d ) , versions )
    map( lambda d : d.update(role_info) , versions )
    resp = { "count": len(versions),
             "cur_page": len(versions),
             "num_pages": len(versions),
             "next": None,
             "previous": None,
             "results": versions
             }
    return flask.jsonify(resp)

@app.route("/<rolename>/<roleversion>.tar.gz")
def download(rolename, roleversion):
    srcdir = os.path.join( flask.current_app.appconfig['roles_dir'] , rolename )
    return flask.send_from_directory( srcdir , "%s.tar.gz" % roleversion )

@app.route("/<rolename>/<roleversion>", methods=['PUT'])
def upload(rolename, roleversion):
    if flask.request.content_type != 'application/x-www-form-urlencoded' :
        return flask.jsonify({'msg': "Wrong content type '%s'" % flask.request.content_type.split(';')[0]}) , 405
    roledir = os.path.join( flask.current_app.appconfig['roles_dir'] , rolename )
    matched_role = flask.current_app.roles.by_name( rolename )
    if matched_role :
        matched_version = filter( lambda d : d['name'] == roleversion , matched_role[0]['summary_fields']['versions'] )
        if matched_version :
            return flask.jsonify({'msg': "Role %s with version %s already exists" % ( rolename , roleversion ) }) , 409
    if not os.path.isdir( roledir ) :
        os.mkdir( roledir )
    destination = os.path.join( roledir , "%s.tar.gz" % roleversion )
    if os.path.isfile( destination ) :
        return flask.jsonify({'msg': "File for %s %s already exists" % ( rolename , roleversion ) }) , 409
    with open( destination , 'w' ) as fd :
        fd.write( flask.request.data )
    if matched_role :
         matched_role[0]['summary_fields']['versions'].append( { 'name':roleversion } )
    else :
        _roles = iter([ application.galaxy_role( destination ) ])
        flask.current_app.roles.add_roles( _roles )
    return flask.jsonify({'msg': 'Done'}) , 201


