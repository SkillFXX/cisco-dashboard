#!/bin/sh
set -e
# Les volumes existants peuvent appartenir à root : corriger puis abaisser les privilèges
chown -R app:app /data
exec setpriv --reuid=app --regid=app --init-groups "$@"
