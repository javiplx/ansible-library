#!/usr/bin/python

import flask
import tarfile
import yaml
import operator, itertools
import os

me = { "description": "ansible-library REST API",
       "current_version": "v1",
       "available_versions": {"v1": "/api/v1/"}
       }

app = flask.Flask('ansible-library')

@app.route("/api/")
def api():
    return flask.jsonify(me)

@app.route("/api/v1/roles/")
def get_roles():
    user = flask.request.args.get('owner__username')
    name = flask.request.args.get('name')
    roles = filter( lambda d : d['name'] == name , read_roles() )
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
    role = filter( lambda d : d['id'] == id , read_roles() )
    if len(role) == 0 :
       return "ERROR" , 404
    versions = role[0]['summary_fields']['versions']
    server_name = "%s://%s" % ( flask.request.scheme , flask.request.headers['Host'] )
    role_info = { 'summary_fields': { "role": { "id": role[0]['id'] , "name": role[0]['name'] } } }
    map( lambda d : d.update({'url': "%s/%s/%s.tar.gz" % (server_name,role[0]['name'],d['name'])}) , versions )
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
    roles_dir = '/var/lib/galaxy'
    srcdir = os.path.join( roles_dir , rolename )
    return flask.send_from_directory( srcdir , "%s.tar.gz" % roleversion )


def read_roles () :
    _roles = []
    roles_dir = '/var/lib/galaxy'
    for root, dirs, files in os.walk(roles_dir) :
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
    roles = []
    _roles = sorted( _roles , key=operator.itemgetter('name') )
    for k, g in itertools.groupby(_roles, operator.itemgetter('name')):
        _role = { 'id': _id }
        _role.update( g.next() )
        _role['versions'] = [ { 'name': _role.pop('version') } ]
        for r in g :
          _role['versions'].append( { 'name': r.pop('version') } )
        roles.append( _role )
        _role['summary_fields'] = { 'dependencies': _role.pop('dependencies'),
                                    'versions': _role.pop('versions')
                                    }
        _id += 1
    return roles


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3333, debug=True)

