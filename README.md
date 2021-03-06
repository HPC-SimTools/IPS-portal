# IPS Portal

## Run in development mode

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
