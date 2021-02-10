#!/bin/bash
rand=$RANDOM

curl -X POST -H "Content-Type: application/json" -d '{"code": "Framework", "eventtype": "IPS_START", "ok": true, "comment": "Starting IPS Simulation", "walltime": "0.01", "state": "Running", "stopat": "2021-02-09|14:15:53EST", "rcomment": "Test '${rand}'", "phystimestamp": -1, "portal_runid": "'${HOSTNAME}'_'${rand}'", "seqnum": 0}' 127.0.0.1:5000

curl -X POST -H "Content-Type: application/json" -d '{"code": "Framework", "eventtype": "IPS_RESOURCE_ALLOC", "ok": true, "comment": "Simulation Ended", "walltime": "0.09", "state": "Running", "stopat": "2021-02-09|14:15:53EST", "sim_name": "Test '${rand}'", "phystimestamp": 0, "portal_runid": "'${HOSTNAME}'_'${rand}'", "seqnum": 1}' 127.0.0.1:5000

curl -X POST -H "Content-Type: application/json" -d '{"code": "Framework", "eventtype": "IPS_END", "ok": true, "comment": "Simulation Ended", "walltime": "0.09", "state": "Completed", "stopat": "2021-02-09|14:15:53EST", "sim_name": "Test '${rand}'", "phystimestamp": 999, "portal_runid": "'${HOSTNAME}'_'${rand}'", "seqnum": 2}' 127.0.0.1:5000
