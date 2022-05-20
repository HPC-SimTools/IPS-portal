export PYTHONPATH=$PWD
ips.py --config=sim.conf --platform=platform.conf
curl http://localhost/api/run/0
