#!/usr/bin/env python

from pymongo import MongoClient
from random import choice, randint
import time
import os


client = MongoClient('mongodb://'+os.environ['MONGODB_HOSTNAME']+':27017')
db = client.portal
db.run.drop()
db.event.drop()

user = ['alice', 'bob', 'carol', 'dave', 'eve', 'frank', 'grace']
nrun = 1000
nevent = 100

for run in range(nrun):
    portal_id = str(randint(0, 1e18))
    r = {
        'runid': run,
        'portal_runid': portal_id,
        'user': choice(user),
        'host': 'node{}'.format(randint(1, 1000)),
        'state': 'Completed',
        'rcomment': f"This is run {run}",
        'tokamak': 'tokamak',
        'shotno': randint(1, 1000),
        'simname': 'test data',
        'startat': time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime(time.time()-60*(nrun-run))),
        'stopat': time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime(time.time()-60*(nrun-run-1))),
    }
    db.run.insert_one(r)

    e = {
        'portal_runid': portal_id,
        'created': time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime(time.time()-60*(nrun-run))),
        'seqnum': 0,
        'eventtype': 'IPS_START',
        'code': 'Framework',
        'walltime': 0.0,
        'phystimestamp': -1,
        'comment': 'Starting IPS Simulation',
    }
    db.event.insert_one(e)

    for event in range(nevent):
        e = {
            'portal_runid': portal_id,
            'created': time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime(time.time()-60*(nrun-run-event/nevent))),
            'seqnum': event+1,
            'eventtype': 'COMPONENT_EVENT',
            'code': 'Driver',
            'walltime': 60.0*event/nevent,
            'phystimestamp': event,
            'comment': f'driver step {event}',
        }
        db.event.insert_one(e)

    e = {
        'portal_runid': portal_id,
        'created': time.strftime('%Y-%m-%d|%H:%M:%S%Z', time.localtime(time.time()-60*(nrun-run-1))),
        'seqnum': nevent+1,
        'eventtype': 'IPS_END',
        'code': 'Framework',
        'walltime': 60.0,
        'phystimestamp': nevent-1,
        'comment': 'Simulation Ended',
    }
    db.event.insert_one(e)

    print(f'Created {run} of {nrun}')
