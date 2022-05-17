# IPS Portal

## Run in development mode

Setup environment with conda and install testing requirements

```shell
conda env create -f environment.yml
conda activate ipsportal
conda env update -f environment_dev.yml
```

Install and run the appilcation

```shell
python -m pip install -e .

export FLASK_APP=ipsportal
export MONGODB_HOSTNAME=localhost

# start IPS portal
flask run
```

Go to http://localhost:5000

### Requires mongo

```shell
docker pull mongo:4
docker run --rm -p 27017:27017 -v /tmp/db:/data/db mongo:4
```

### For profile tracing

```shell
docker pull jaegertracing/all-in-one:1.34
docker run --rm -p 9411:9411 -p 16686:16686 --env COLLECTOR_ZIPKIN_HOST_PORT=9411 --env QUERY_BASE_PATH=/jaeger jaegertracing/all-in-one:1.34
```

### To view current state of the mongo db

```shell
docker run --rm --network host -p 8081:8081 -e ME_CONFIG_MONGODB_SERVER=localhost mongo-express
```

then go to http://localhost:8081

## Run with docker in production

## build and run ipsportal

```shell
docker build -t rosswhitfield/ipsportal:latest .
docker run -p 8080:8080 --rm --env MONGODB_HOSTNAME=localhost --network host -t rosswhitfield/ipsportal:latest
```

## To push to dockerhub

```shell
docker push rosswhitfield/ipsportal:latest
```

## Or use docker-compose

```shell
docker-compose up
```

Go to http://localhost:8080

## A docker container to create db backups

```
docker build -f Dockerfile.db-backup -t rosswhitfield/ipsportal-backup:latest .
```
