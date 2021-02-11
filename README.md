# IPS Portal

## Run in developement mode

```shell
python -m pip install -e .

export FLASK_APP=ipsportal

# initialize database
flask init-db

# start IPS portal
flask run
```

Go to http://localhost:5000

## Run with docker in production

```shell
docker build -t ipsportal .
docker run -p 8080:8080 -v /tmp/ips:/usr/var/ipsportal-instance --rm -t ipsportal
```

Go to http://localhost:8080
