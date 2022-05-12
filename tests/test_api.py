from uuid import uuid1


def test_post_events(client):
    current_number_of_runs = len(client.get("/api/runs").json)

    # Post a IPS_START event
    portal_runid = str(uuid1())
    start_event = {
        'code': "Framework",
        'eventtype': "IPS_START",
        "ok": True,
        'comment': f"Starting IPS Simulation {portal_runid}",
        'walltime': "0.01",
        "state": "Running",
        "startat": "2022-05-03|15:41:07EDT",
        "rcomment": f"CI Test {portal_runid}",
        'phystimestamp': -1,
        'portal_runid': portal_runid,
        'seqnum': 0}
    response = client.post("/api/event", json=start_event)

    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == "New run created"
    assert 'runid' in response.json
    runid = response.json['runid']

    new_number_of_runs = len(client.get("/api/runs").json)

    assert new_number_of_runs - current_number_of_runs == 1

    # retrieve run info by runid
    response = client.get(f"/api/run/{runid}")
    assert response.status_code == 200
    assert response.json['portal_runid'] == start_event['portal_runid']
    assert response.json['state'] == start_event['state']
    assert response.json['startat'] == start_event['startat']
    assert response.json['rcomment'] == start_event['rcomment']
    assert response.json['runid'] == runid
    assert not response.json['has_trace']

    # retrieve run info by portal_runid
    response = client.get(f"/api/run/{portal_runid}")
    assert response.status_code == 200
    assert response.json['portal_runid'] == start_event['portal_runid']
    assert response.json['state'] == start_event['state']
    assert response.json['startat'] == start_event['startat']
    assert response.json['rcomment'] == start_event['rcomment']
    assert response.json['runid'] == runid
    assert not response.json['has_trace']

    # Post a IPS_CALL_END event
    event = {
        "code": "Framework",
        "eventtype": "IPS_CALL_END",
        "ok": "True",
        "comment": "Target = sim@driver@2:finalize(0)",
        "walltime": "26.70",
        "trace": {
            "timestamp": 1651606894526459,
            "duration": 156717,
            "localEndpoint": {
                "serviceName": "sim@driver@2"
            },
            "name": "finalize(0)",
            "id": "6daf4d4c1a7bd43b",
            "parentId": "f3994d99c2892c58",
            "traceId": "8b417652fc2d28c301295e8fa03f75c9"
        },
        "sim_name": "sim",
        "phystimestamp": 0,
        "portal_runid": portal_runid,
        "seqnum": 1
    }
    response = client.post("/api/event", json=event)

    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == "Event added to run"

    # check run info, should be unchanged from start except has_trace
    response = client.get(f"/api/run/{portal_runid}")
    assert response.status_code == 200
    assert response.json['portal_runid'] == start_event['portal_runid']
    assert response.json['state'] == start_event['state']
    assert response.json['startat'] == start_event['startat']
    assert response.json['rcomment'] == start_event['rcomment']
    assert response.json['runid'] == runid
    assert response.json['has_trace']

    # Post a IPS_END event
    end_event = {
        'code': "Framework",
        'eventtype': "IPS_END",
        "ok": True,
        'comment': f"Simulation Ended {portal_runid}",
        'walltime': "26.70",
        "state": "Complete",
        "stopat": "2022-05-03|15:41:34EDT",
        'phystimestamp': 1,
        'portal_runid': portal_runid,
        'seqnum': 2,
        "trace": {
            "timestamp": 1651606867984607,
            "duration": 26698980,
            "localEndpoint": {
                "serviceName": "FRAMEWORK@Framework@0"
            },
            "id": "f3994d99c2892c58",
            "tags": {
                "total_cores": "8"
            },
            "traceId": "8b417652fc2d28c301295e8fa03f75c9"
        },
    }

    response = client.post("/api/event", json=end_event)

    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == "Event added to run and run ended"

    # check run info, should be updated
    response = client.get(f"/api/run/{portal_runid}")
    assert response.status_code == 200
    assert response.json['portal_runid'] == end_event['portal_runid']
    assert response.json['state'] == end_event['state']
    assert response.json['startat'] == start_event['startat']
    assert response.json['stopat'] == end_event['stopat']
    assert response.json['runid'] == runid
    assert response.json['has_trace']

    # check events with runid
    response = client.get(f"/api/run/{runid}/events")
    assert response.status_code == 200
    assert len(response.json) == 3
    event0 = response.json[0]
    assert event0.pop('created')
    assert event0 == start_event
    event1 = response.json[1]
    assert event1.pop('created')
    trace1 = event.pop('trace')
    assert event1 == event
    event2 = response.json[2]
    assert event2.pop('created')
    trace2 = end_event.pop('trace')
    assert event2 == end_event

    # check events with portal_runid
    response = client.get(f"/api/run/{portal_runid}/events")
    assert response.status_code == 200
    assert len(response.json) == 3
    event0 = response.json[0]
    assert event0.pop('created')
    assert event0 == start_event
    event1 = response.json[1]
    assert event1.pop('created')
    assert event1 == event
    event2 = response.json[2]
    assert event2.pop('created')
    assert event2 == end_event

    # check trace with runid
    response = client.get(f"/api/run/{runid}/trace")
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0] == trace1
    assert response.json[1] == trace2

    # check trace with portal_runid
    response = client.get(f"/api/run/{portal_runid}/trace")
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0] == trace1
    assert response.json[1] == trace2


def test_invalid_portal_id(client):
    # this isn't a IPS_START event so this portal_runid is invalid
    portal_runid = str(uuid1())

    event = {
        "code": "Framework",
        "eventtype": "IPS_CALL_END",
        "comment": "Target = sim@driver@2:finalize(0)",
        "walltime": "1.0",
        "phystimestamp": 0,
        "portal_runid": portal_runid,
        "seqnum": 1
    }
    response = client.post("/api/event", json=event)

    assert response.status_code == 400
    assert "message" in response.json
    assert response.json["message"] == "Invalid portal_runid"

    event = {
        "code": "Framework",
        "eventtype": "IPS_CALL_END",
        "comment": "Target = sim@driver@2:finalize(0)",
        "walltime": "1.0",
        "phystimestamp": 0,
        "portal_runid": portal_runid,
        "seqnum": 1,
        "trace": {"timestamp": 1651606867984607}
    }
    response = client.post("/api/event", json=event)

    assert response.status_code == 400
    assert "message" in response.json
    assert response.json["message"] == "Invalid portal_runid"


def test_missing_json(client):
    response = client.post("/api/event", json={})
    assert response.status_code == 400
    assert response.json['message'] == "Missing required data: "\
        "['code', 'comment', 'eventtype', 'phystimestamp', 'portal_runid', 'seqnum', 'walltime']"

    response = client.post("/api/event",
                           json={"code": "Framework",
                                 "eventtype": "IPS_CALL_END",
                                 "comment": "Target = sim@driver@2:finalize(0)",
                                 "walltime": "1.0",
                                 "phystimestamp": 0})
    assert response.status_code == 400
    assert response.json['message'] == "Missing required data: ['portal_runid', 'seqnum']"


def test_duplicate_portal_runid(client):
    # Try sending two IPS_START events with the same portal_runid
    portal_runid = str(uuid1())

    start_event = {
        'code': "Framework",
        'eventtype': "IPS_START",
        "ok": True,
        'comment': f"Starting IPS Simulation {portal_runid}",
        'walltime': "0.01",
        "state": "Running",
        "startat": "2022-05-03|15:41:07EDT",
        "rcomment": f"CI Test {portal_runid}",
        'phystimestamp': -1,
        'portal_runid': portal_runid,
        'seqnum': 0}
    response = client.post("/api/event", json=start_event)

    assert response.status_code == 200
    assert "message" in response.json
    assert response.json["message"] == "New run created"
    assert 'runid' in response.json

    # this should fail
    response = client.post("/api/event", json=start_event)
    assert response.status_code == 400
    assert "message" in response.json
    assert response.json["message"] == "Duplicate portal_runid Key"
    assert 'runid' not in response.json


def test_runid_not_found(client):
    response = client.get("/api/run/10000000")
    assert response.status_code == 404
    assert response.json['message'] == "runid 10000000 not found"

    response = client.get("/api/run/10000000/events")
    assert response.status_code == 404
    assert response.json['message'] == "runid 10000000 not found"

    response = client.get("/api/run/10000000/trace")
    assert response.status_code == 404
    assert response.json['message'] == "runid 10000000 not found"


def test_portal_runid_not_found(client):
    portal_runid = str(uuid1())
    response = client.get(f"/api/run/{portal_runid}")
    assert response.status_code == 404
    assert response.json['message'] == f"portal_runid {portal_runid} not found"

    response = client.get(f"/api/run/{portal_runid}/events")
    assert response.status_code == 404
    assert response.json['message'] == f"portal_runid {portal_runid} not found"

    response = client.get(f"/api/run/{portal_runid}/trace")
    assert response.status_code == 404
    assert response.json['message'] == f"portal_runid {portal_runid} not found"
