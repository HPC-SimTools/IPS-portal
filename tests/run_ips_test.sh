#!/bin/bash
cd ips_test
export PYTHONPATH=$PWD
ips.py --config=sim.conf --platform=platform.conf

newest_runid=$(curl http://localhost/api/runs | jq .[-1].runid)
run_json=$(curl http://localhost/api/run/$newest_runid)

# state
if [ $(echo $run_json | jq .state) != '"Completed"' ]; then echo "state"; exit 1; fi
# simname
if [ $(echo $run_json | jq .simname) != '"simulation"' ]; then echo "simname"; exit 1; fi
# rcomment
if [ $(echo $run_json | jq .rcomment) != '"This-is-just-a-test"' ]; then
    echo "rcomment";
    exit 1;
fi

events=$(curl http://localhost/api/run/$newest_runid/events)

# last event
echo $events | jq .[-1]
