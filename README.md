# IPS Portal

Documentation for how to use IPS-framework with this IPS-portal can be found at https://ips-framework.readthedocs.io/en/latest/user_guides/portal_guides.html

## Run in development mode

Setup environment with python venv and install IPS-portal:

```shell
python -m venv env
source env/bin/activate
python -m pip install -e .[dev]
```

If that fails with `ERROR: File "setup.py" not found.` try upgrading pip first:

```shell
python -m pip install --upgrade pip
```

To run the application in debug mode

```shell
export FLASK_APP=ipsportal
export FLASK_DEBUG=True

# start IPS portal
flask run
```

Go to http://localhost:5000

### Requires mongo

```shell
docker run --rm -p 27017:27017 -v /tmp/db:/data/db mongo:4
```

### For profile tracing

```shell
docker run --rm -p 9411:9411 -p 16686:16686 --env COLLECTOR_ZIPKIN_HOST_PORT=9411 --env QUERY_BASE_PATH=/jaeger jaegertracing/all-in-one:1.35
```

### To view current state of the mongo db

```shell
docker run --rm --network host -p 8081:8081 -e ME_CONFIG_MONGODB_SERVER=localhost mongo-express
```

then go to http://localhost:8081

## Run with docker

```shell
docker-compose up --build
```

Go to http://localhost


---
[![CI](https://github.com/HPC-SimTools/IPS-portal/actions/workflows/workflows.yml/badge.svg)](https://github.com/HPC-SimTools/IPS-portal/actions/workflows/workflows.yml)
[![codecov](https://codecov.io/gh/HPC-SimTools/IPS-portal/branch/main/graph/badge.svg)](https://codecov.io/gh/HPC-SimTools/IPS-portal)
