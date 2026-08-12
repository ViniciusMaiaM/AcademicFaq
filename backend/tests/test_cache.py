from repositories.cache import cache_rp


def test_cache_stats_empty(client, auth_headers):
    resp = client.get("/api/v1/cache/stats", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cache_size"] == 0
    assert body["most_accessed"] == []


def test_cache_stats_with_real_entries(client, auth_headers, db_session):
    cache_rp.upsert(db_session, "hash1", "Quando começam as aulas?", "17/03/2025.", [])
    cache_rp.upsert(db_session, "hash2", "Quantas horas tem o TCC?", "90 horas.", [])
    cache_rp.increment_access(db_session, "hash1")
    cache_rp.increment_access(db_session, "hash1")

    resp = client.get("/api/v1/cache/stats", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["cache_size"] == 2
    assert len(body["most_accessed"]) == 2
    top = body["most_accessed"][0]
    assert top["question"] == "Quando começam as aulas?"
    assert top["access_count"] == 3  # 1 no upsert + 2 increments


def test_cache_clear(client, auth_headers, db_session):
    cache_rp.upsert(db_session, "hash1", "pergunta", "resposta", [])
    assert cache_rp.get_stats(db_session)["cache_size"] == 1

    resp = client.delete("/api/v1/cache/clear", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    resp_stats = client.get("/api/v1/cache/stats", headers=auth_headers)
    assert resp_stats.json()["cache_size"] == 0


def test_cache_routes_require_auth(client):
    assert client.get("/api/v1/cache/stats").status_code == 422
    assert client.delete("/api/v1/cache/clear").status_code == 422
