#!/usr/bin/python

import flask

me = { "description": "ansible-library REST API",
       "current_version": "v1",
       "available_versions": {"v1": "/api/v1/"}
       }

roles = [
          { "id": 1,
            "username": "Feverup",
            "name": "augeas",
            "description": "Partial implementation of augeas commands",
            "versions": [{"name": "v0.9"}, {"name": "v0.1"}],
            "dependencies": [],
            "min_ansible_version": "1.2"
            }
          ]

versions = [
             { "id": 2,
               "name": "v0.9",
               "summary_fields": {"role": {"id": 1, "name": "augeas"}},
               "url": ""
               },
             { "id": 3,
               "name": "v0.1",
               "summary_fields": {"role": {"id": 2, "name": "augeas"}},
               "url": ""
               }
             ]

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3333, debug=True)

