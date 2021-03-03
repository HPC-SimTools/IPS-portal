#!/bin/bash -x

# create random secret key
python3 -c "import random,string;print('SECRET_KEY = \"'+''.join(random.choices(string.ascii_letters, k=64))+'\"')" > /usr/var/ipsportal-instance/config.py

exec "$@"
