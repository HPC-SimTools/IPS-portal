def test_post_invalid_event(client):
    response = client.post("/", json={})
    assert response.text == "failed"
    assert response.status_code == 400
