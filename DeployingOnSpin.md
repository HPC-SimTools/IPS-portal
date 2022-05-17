Deploy
 - Name: db
 - Docker Image: mongo:4
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
 - Docker Image: jaegertracing/all-in-one:1.31
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
