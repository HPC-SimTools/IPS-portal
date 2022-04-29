from uuid import uuid1


def test_post_invalid_event(client):
    response = client.post("/", json={})
    assert response.text == "failed"
    assert response.status_code == 400


def test_post_event(client):
    portal_runid = str(uuid1())
    response = client.post("/", json={'code': "Framework",
                                      'eventtype': "IPS_START",
                                      "ok": True,
                                      'comment': f"Starting IPS Simulation {portal_runid}",
                                      'walltime': "0.01",
                                      "state": "Running",
                                      "stopat": "2021-02-09|14:15:53EST",
                                      "rcomment": f"CI Test {portal_runid}",
                                      'phystimestamp': -1,
                                      'portal_runid': portal_runid,
                                      'seqnum': 0})
    assert response.text == "success"
    assert response.status_code == 200

    response = client.post("/", json={'code': "Framework",
                                      'eventtype': "IPS_END",
                                      "ok": True,
                                      "comment": f"Simulation Ended {portal_runid}",
                                      'walltime': "0.09",
                                      "state": "Completed",
                                      "stopat": "2021-02-09|14:15:53EST",
                                      "sim_name": "CI Test '",
                                      'phystimestamp': 1,
                                      'portal_runid': portal_runid,
                                      'seqnum': 1})
    assert response.text == "success"
    assert response.status_code == 200

    response = client.get("/")
    assert response.status_code == 200
    assert f"CI Test {portal_runid}" in response.text

    response = client.get("/0")
    assert response.status_code == 200
    assert f"CI Test {portal_runid}" in response.text
    assert f"Starting IPS Simulation {portal_runid}" in response.text
    assert f"Simulation Ended {portal_runid}" in response.text
