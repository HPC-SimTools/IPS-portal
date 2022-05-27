#!/bin/bash
cd ips_test
ips.py --version
ips.py --config=sim.conf --platform=platform.conf

newest_runid=$(curl -s http://localhost/api/runs | jq .[-1].runid)
run_json=$(curl -s http://localhost/api/run/$newest_runid)
# check if trace information exist, it does for IPS >= 0.6.0
has_trace=$(python -c "import ipsframework; print('no') if ipsframework.__version__ in [\"0.3.0\", \"0.4.1\", \"0.5.0\"] else print('yes')")

# state
if [ $(echo $run_json | jq .state) != '"Completed"' ]; then echo "state"; exit 1; fi
# simname
if [ $(echo $run_json | jq .simname) != '"simulation"' ]; then echo "simname"; exit 1; fi
# rcomment
if [ $(echo $run_json | jq .rcomment) != '"This-is-just-a-test"' ]; then echo "rcomment"; exit 1; fi

events=$(curl -s http://localhost/api/run/$newest_runid/events)

# Check number of events
if [ $has_trace == "yes" ]; then
    if [ $(echo $events | jq length) -ne 12 ]; then echo "number_of_events"; exit 1; fi
else
    if [ $(echo $events | jq length) -ne 6 ]; then echo "number_of_events"; exit 1; fi
fi

# check last event

# code
if [ $(echo $events | jq .[-1].code) != '"Framework"' ]; then echo "code"; exit 1; fi
# eventtype
if [ $(echo $events | jq .[-1].eventtype) != '"IPS_END"' ]; then echo "eventtype"; exit 1; fi
# sim_name
if [ $(echo $events | jq .[-1].sim_name) != '"simulation"' ]; then echo "sim_name"; exit 1; fi
# state
if [ $(echo $events | jq .[-1].state) != '"Completed"' ]; then echo "state"; exit 1; fi

# check trace information
trace=$(curl -s http://localhost/api/run/$newest_runid/trace)

if [ $has_trace == "yes" ]; then
    # Check number of events
    if [ $(echo $trace | jq length) -ne 5 ]; then echo "yes number_of_traces"; exit 1; fi
    # Service name
    if [ $(echo $trace | jq .[-1].localEndpoint.serviceName) != '"FRAMEWORK@Framework@0"' ]; then echo "localEndpoint.serviceName"; exit 1; fi
else
    # Check number of events
    if [ $(echo $trace | jq length) -ne 0 ]; then echo "no number_of_traces"; exit 1; fi
fi
