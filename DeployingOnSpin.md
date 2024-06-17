# Deploying on Spin

## Manual deploy

Deploy
 - Name: db
 - Docker Image: mongo:6
 - Namespace: ipsportal
 - Environment Variables
   - Add Variable
     - MONGO_INITDB_ROOT_USERNAME: mongo
     - MONGO_INITDB_ROOT_PASSWORD: password
 - Volume:
   - Add Volume: Add a new persistent volume (claim)
     - Name: mongodb
     - Storage Class: nfs-client
     - Capacity: 1 GiB
     - Mount Point: /data/db
 - Scaling/Upgrade Policy
   - Rolling: stop old pods, then start new
 - Secutiry & Host Config
   - Drop Capabilties
     - ALL
   - Add Capabilities
     - CHOWN
     - DAC_OVERRIDE
     - FOWNER
     - SETGID
     - SETUID

Deploy
 - Name: ipsportal
 - Docker Image: rosswhitfield/ipsportal:latest
 - Namespace: ipsportal
 - Environment Variables
   - Add Variable
     - MONGO_HOST: db
     - MONGO_USERNAME: mongo
     - MONGO_PASSWORD: password
     - JAEGER_HOST: jaeger
 - Secutiry & Host Config
   - Drop Capabilties
     - ALL

Deploy
 - Name: db-backup
 - Docker Image: rosswhitfield/ipsportal-backup:latest
 - Namespace: ipsportal
 - Environment Variables
   - Add Variable
     - MONGODB_HOSTNAME: db
 - Volume:
   - Add Volume: Bind-mount a directory from the node
     - Name: backup
     - Path on the Node: /global/u1/r/rwp/ipsportal_backup
     - The Path on the Node must be: An existing directory
     - Mount Point: /backup
 - Command:
   - User ID: `id`
   - Filesystem Group: `gid`
 - Secutiry & Host Config
   - Run as Non-Root: Yes
   - Drop Capabilties
     - ALL
   - Add Capabilities
     - NET_BIND_SERVICE

Jaeger
 - Name: jaeger
 - Docker Image: jaegertracing/all-in-one:1.38
 - Namespace: ipsportal
 - Environment Variables
   - Add Variable
     - COLLECTOR_ZIPKIN_HOST_PORT: 9411
     - QUERY_BASE_PATH: /jaeger
 - Secutiry & Host Config
   - Drop Capabilties
     - ALL

Add Ingress
 - Name: lb
 - Namespace: ipsportal
 - Specify a hostname to use
   - Request Host: lb.ipsportal.development.svc.spin.nersc.org
 - Paths:
   - /
     - Target: ipsportal
     - Port: 8080
   - /jaeger
     - Target: jaeger
     - Port: 16686

## Deploy with Kubernetes manifest

Log in to spin rancher, see https://docs.nersc.gov/services/spin/rancher2/cli/

To see which cluster you are on:

```shell
rancher context current
```

To switch between production and development clusters:

```shell
rancher context switch
```

Create the `ipsportal` namespace:

```shell
rancher namespace create ipsportal
```

Set up secrets from example YAML file, update `ipsportal.yaml` before running, base64 encode, e.g. `echo -n "password" | base64`. Update bearer-token from https://rancher2.spin.nersc.gov/apikeys

Deploy:

```shell
rancher kubectl apply -f ipsportal-secrets.yaml -f ipsportal.yaml
```

### Backup

To manually trigger a database backup run

```shell
rancher kubectl create job --from=cronjob/mongodb-dump manual-dump --namespace=ipsportal
```

then to see the status of the job run

```shell
rancher kubectl describe job.batch/manual-dump --namespace=ipsportal
```

you can delete the jobs by

```shell
rancher kubectl delete job manual-dump --namespace=ipsportal
```

To restore from backup archive: upload to pod, extract, restore:

```shell
rancher kubectl get pods --namespace=ipsportal # get db pod name
rancher kubectl cp mongodb-dump.archive.gz ipsportal/{pod-name}:/tmp
rancher kubectl exec {pod-name} --namespace=ipsportal -- gunzip /tmp/mongodb-dump.archive.gz
rancher kubectl exec {pod-name} --namespace=ipsportal -- mongorestore --archive=/tmp/mongodb-dump.archive --authenticationDatabase admin --username mongo --password password-CHANGE-ME
```

### TLS

To setup tls certs with letsencrypt make sure bearer-token is correct and `CONTEXT`, `DOMAIN` is correct for prod/dev cluster.

Temporary change command to `/scripts/setup.sh` and run once to do initial setup

```shell
rancher kubectl --namespace=ipsportal create job --from=cronjob/certbot certbot-setup
```

Then change the command back to `/scripts/renew.sh`

After go to the Load Balancer and select `letencrypt` certificate.
