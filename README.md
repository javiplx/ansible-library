
# Ansible Library

Ansible Library is a minimal galaxy implementation, intended to allow serving
(private) roles from local storage and behave as proxy towards ansible galaxy.

It is intended to allow role installs with standard tools, although it requires
a minor patch to ansible-galaxy, that enables

    ansible-galaxy install --server=http://local-galaxy:3333 private-role,v1.4

## Usage

Just download the server in your prefered location and run

    $ ansible-library.py

which starts the server listening on port 3333.

On startup, it searchs all files under `/var/lib/galaxy`, and uses the presence
of `meta/main.yml` is used to decide whether it is a role or not. The name and
version are assigned following the github download standards, that is

    /var/lib/galaxy/<rolename>/<roleversion>.tar.gz

although it is possible to use `name` or `version` non-standard entries under
`galaxy_info` for that purpose, to give more flexibility to the storage layout.

