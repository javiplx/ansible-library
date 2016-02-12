#!/usr/bin/python

import flask
import tarfile
import yaml
import os

me = { "description": "ansible-library REST API",
       "current_version": "v1",
       "available_versions": {"v1": "/api/v1/"}
       }

roles = []
versions = []

app = flask.Flask('ansible-library')

@app.route("/api/")
def api():
    return flask.jsonify(me)

@app.route("/api/v1/roles/")
def get_roles():
    user = flask.request.args.get('owner__username')
    name = flask.request.args.get('name')
    resp = { "count": len(roles),
             "cur_page": len(roles),
             "num_pages": len(roles),
             "next": None,
             "previous": None,
             "results": roles
             }
    return flask.jsonify(resp)

@app.route("/api/v1/roles/<id>/versions/")
def get_versions(id):
    resp = { "count": len(versions),
             "cur_page": len(versions),
             "num_pages": len(versions),
             "next": None,
             "previous": None,
             "results": versions
             }
    return flask.jsonify(resp)


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
            _roles.append( yaml.load(tar.extractfile(meta[0])) )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3333, debug=True)

