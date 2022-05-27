#!/bin/bash -x

# create random secret key
python -c 'import secrets; print(f"SECRET_KEY = \"{secrets.token_hex()}\"")' > /usr/local/var/ipsportal-instance/config.py

exec "$@"
