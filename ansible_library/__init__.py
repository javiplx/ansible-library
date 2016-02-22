
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

import ansible_library.application
import flask
import os
import time

from ansible.module_utils.urls import open_url

me = { "description": "ansible-library REST API",
       "current_version": "v1",
       "available_versions": {"v1": "/api/v1/"}
       }

app = ansible_library.application.library()

@app.route("/api/")
def api():
    return flask.jsonify(me)

@app.before_request
def before_request():
    now = time.time()
    for role in flask.current_app.galaxy :
        if now - role[1].tstamp > app.ttl :
            flask.current_app.galaxy.remove( role )

@app.route("/api/v1/roles/")
def get_roles():
    user = flask.request.args.get('owner__username')
    name = flask.request.args.get('name')
    roles = filter( lambda d : d[1]['name'] == name , flask.current_app.roles + flask.current_app.galaxy )
    if not roles :
        galaxy_url = "https://galaxy.ansible.com%s" % flask.request.full_path
        response = flask.json.load(open_url(galaxy_url))
        results = map( lambda x : ( time.time() , application.proxied_role(x) ) , response['results'] )
        flask.current_app.galaxy.extend( results )
        return flask.jsonify(response)
    resp = { "count": len(roles),
             "cur_page": len(roles),
             "num_pages": len(roles),
             "next": None,
             "previous": None,
             "results": map( lambda x : x[1] , roles )
             }
    return flask.jsonify(resp)

@app.route("/api/v1/roles/<int:id>/versions/")
def get_versions(id):
    role = filter( lambda d : d[1]['id'] == id , flask.current_app.roles + flask.current_app.galaxy )
    if len(role) == 0 :
        galaxy_url = "https://galaxy.ansible.com%s" % flask.request.full_path
        return open_url(galaxy_url).read()
    versions = role[0][1]['summary_fields']['versions']
    role_info = { 'summary_fields': { "role": { "id": role[0][1]['id'] , "name": role[0][1]['name'] } } }
    map( lambda d : d.update({'url': ""}) , versions )
    if filter( lambda d : d[1]['id'] == id , flask.current_app.roles ) :
        map( lambda d : d.update({'url': "%s%s/%s.tar.gz" % (flask.request.url_root,role[0][1]['name'],d['name'])}) , versions )
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
    srcdir = os.path.join( flask.current_app.roles_dir , rolename )
    return flask.send_from_directory( srcdir , "%s.tar.gz" % roleversion )


