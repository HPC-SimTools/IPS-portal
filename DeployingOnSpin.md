Deploy
 - Name: db
 - Docker Image: mongo:4
 - Namespace: ipsportal
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
     - MONGODB_HOSTNAME: db
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

Add Ingress
 - Name: lb
 - Namespace: ipsportal
 - Specify a hostname to use
   - Request Host: lb.ipsportal.development.svc.spin.nersc.org
 - Target: ipsportal
 - Port: 8080
