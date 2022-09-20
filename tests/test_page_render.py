from uuid import uuid1
import hashlib
import os
import requests


def test_post_invalid_run_number(client):
    run = 999999
    response = client.get(f"/{run}")
    assert response.status_code == 404
    assert f"Run - {run}" in response.text
    assert "Not found" in response.text


def test_post_event(client):
    portal_runid = str(uuid1())
    traceID = hashlib.md5(portal_runid.encode()).hexdigest()

    response = client.post("/", json={
        'code': "Framework",
        'eventtype': "IPS_START",
        "ok": True,
        'comment': f"Starting IPS Simulation {portal_runid}",
        'walltime': "0.01",
        "state": "Running",
        "stopat": "2021-02-09|14:15:53EST",
        "rcomment": f"CI Test {portal_runid}",
        'phystimestamp': -1,
        'portal_runid': portal_runid,
        'seqnum': 0,
        'simname': 'CI Test'
    }
    )
    assert response.status_code == 200
    assert response.json['message'] == 'New run created and 1 events added to run'
    runid = response.json['runid']

    response = client.post("/", json={
        "code": "WORKER__worker",
        "eventtype": "IPS_TASK_END",
        "ok": "True",
        "walltime": "24.66",
        "trace": {
            "timestamp": 1647005427615235,
            "duration": 2153081,
            "localEndpoint": {
                "serviceName": "/bin/sleep"
            },
            "name": "2.0",
            "id": "8a064c788269e0b1",
            "parentId": "4f44682177c5b766",
            "tags": {
                "procs_requested": "1",
                "cores_allocated": "1"
            },
            "traceId": traceID
        },
        "state": "Running",
        "comment": "task_id = 60  elapsed time = 2.15 S",
        "sim_name": "sim",
        "phystimestamp": -1,
        "portal_runid": portal_runid,
        "seqnum": 1
    }
    )

    assert response.status_code == 200
    assert response.json['message'] == "1 events added to run"

    response = client.post("/", json={
          "code": "Framework",
          "eventtype": "IPS_CALL_END",
          "ok": "True",
          "comment": "Target = sim@driver@2:step(0)",
          "walltime": "26.81",
          "trace": {
                  "timestamp": 1647005405413568,
                  "duration": 26499127,
                  "localEndpoint": {
                            "serviceName": "sim@driver@2"
                          },
                  "name": "step(0)",
                  "id": "4f44682177c5b766",
                  "parentId": "f3994d99c2892c58",
                  "traceId": traceID
                },
          "sim_name": "CI Test",
          "phystimestamp": 0,
          "portal_runid": portal_runid,
          "seqnum": 2
        }
    )
    assert response.status_code == 200
    assert response.json['message'] == "1 events added to run"

    response = client.post("/", json={
        'code': "Framework",
        'eventtype': "IPS_END",
        "ok": True,
        "comment": f"Simulation Ended {portal_runid}",
        'walltime': "27.0",
        "state": "Completed",
        "stopat": "2021-02-09|14:15:53EST",
        "sim_name": "CI Test",
        'phystimestamp': 1,
        'portal_runid': portal_runid,
        'seqnum': 3,
        "trace": {
            "timestamp": 1647005405104414,
            "duration": 26995801,
            "localEndpoint": {
                "serviceName": "FRAMEWORK@Framework@0"
            },
            "id": "f3994d99c2892c58",
            "tags": {
                "total_cores": "8"
            },
            "traceId": traceID
        }
    })

    assert response.status_code == 200
    assert response.json['message'] == "1 events added to run and run ended"

    response = client.get("/")
    assert response.status_code == 200

    response = client.get(f"/{runid}")
    assert response.status_code == 200
    assert f"CI Test {portal_runid}" in response.text
    assert f"IPS Portal - Run - {runid}" in response.text
    assert f"runid={runid}" in response.text

    response = client.get(f"/resource_plot/{runid}")
    assert response.status_code == 200
    assert f"<a href='/{runid}'>Run - {runid}</a> Sim Name: CI Test Comment: " \
        f"CI Test {portal_runid}<br>Allocation total cores = 8" in response.text

    response = client.get(f"/gettrace/{runid}")
    assert response.status_code == 302
    assert f"/jaeger/trace/{traceID}" in response.text

    # check trace was sent to jaeger
    r = requests.get(f"http://{os.environ.get('JAEGER_HOST', 'localhost')}:16686/jaeger/api/traces/{traceID}")
    assert "data" in r.json()
    assert "traceID" in r.json()["data"][0]
    assert r.json()["data"][0]["traceID"] == traceID
