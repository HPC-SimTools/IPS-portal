#!/bin/bash -x

# initialize database if it doesn't exist
FLASK_APP=ipsportal flask init-db 2> /dev/null || true

# create random password if it doesn't exist
if [ ! -e /usr/var/ipsportal-instance/config.py ]; then
    python3 -c "import random,string;print('SECRET_KEY = \"'+''.join(random.choices(string.ascii_letters, k=64))+'\"')" > /usr/var/ipsportal-instance/config.py
fi

exec "$@"
