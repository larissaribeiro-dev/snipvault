def payload(**overrides):
    data = {
        "title": "Ler arquivo em chunks",
        "description": "Evita carregar tudo na memória",
        "language": "Python",
        "code": "with open(path, 'rb') as f:\n    while chunk := f.read(8192):\n        ...",
        "is_public": False,
        "tags": ["io", "Files"],
    }
    return {**data, **overrides}


def create(client, headers, **overrides):
    response = client.post("/snippets", json=payload(**overrides), headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_requires_auth(client):
    assert client.post("/snippets", json=payload()).status_code == 401


def test_create_normalizes_language_and_tags(client, auth):
    snippet = create(client, auth, tags=["Files", "io", "files", " io "])

    assert snippet["language"] == "python"
    assert snippet["tags"] == ["files", "io"]
    assert snippet["is_public"] is False


def test_create_rejects_empty_code(client, auth):
    response = client.post("/snippets", json=payload(code=""), headers=auth)

    assert response.status_code == 422


def test_create_rejects_invalid_tag(client, auth):
    response = client.post("/snippets", json=payload(tags=["tem espaço"]), headers=auth)

    assert response.status_code == 422


def test_create_rejects_too_many_tags(client, auth):
    tags = [f"tag{i}" for i in range(11)]
    response = client.post("/snippets", json=payload(tags=tags), headers=auth)

    assert response.status_code == 422


def test_tags_are_shared_between_snippets(client, auth):
    first = create(client, auth, tags=["io"])
    second = create(client, auth, title="Outro", tags=["io"])

    assert first["tags"] == second["tags"] == ["io"]


def test_list_returns_only_own_snippets(client, auth, other_auth):
    create(client, auth, title="da ana")
    create(client, other_auth, title="do bruno")

    body = client.get("/snippets", headers=auth).json()

    assert body["total"] == 1
    assert body["items"][0]["title"] == "da ana"


def test_list_orders_newest_first_and_paginates(client, auth):
    for i in range(5):
        create(client, auth, title=f"snippet {i}")

    page = client.get("/snippets", params={"limit": 2, "offset": 1}, headers=auth).json()

    assert page["total"] == 5
    assert page["limit"] == 2 and page["offset"] == 1
    assert [s["title"] for s in page["items"]] == ["snippet 3", "snippet 2"]


def test_list_rejects_invalid_pagination(client, auth):
    assert client.get("/snippets", params={"limit": 0}, headers=auth).status_code == 422
    assert client.get("/snippets", params={"limit": 101}, headers=auth).status_code == 422
    assert client.get("/snippets", params={"offset": -1}, headers=auth).status_code == 422


def test_filter_by_language_and_tag(client, auth):
    create(client, auth, title="py", language="python", tags=["io"])
    create(client, auth, title="go", language="go", tags=["io", "http"])

    by_language = client.get("/snippets", params={"language": "GO"}, headers=auth).json()
    by_tag = client.get("/snippets", params={"tag": "http"}, headers=auth).json()

    assert [s["title"] for s in by_language["items"]] == ["go"]
    assert [s["title"] for s in by_tag["items"]] == ["go"]


def test_search_matches_title_description_and_code(client, auth):
    create(client, auth, title="Retry com backoff", description=None, code="sleep(2 ** n)")
    create(client, auth, title="Outro", description="usa backoff exponencial", code="x = 1")
    create(client, auth, title="Terceiro", description=None, code="print('backoff')")
    create(client, auth, title="Nada a ver", description=None, code="y = 2")

    body = client.get("/snippets", params={"q": "backoff"}, headers=auth).json()

    assert body["total"] == 3


def test_search_treats_wildcards_literally(client, auth):
    create(client, auth, title="desconto de 50% hoje", code="a")
    create(client, auth, title="sem percentual", code="b")

    body = client.get("/snippets", params={"q": "50%"}, headers=auth).json()

    assert [s["title"] for s in body["items"]] == ["desconto de 50% hoje"]


def test_owner_reads_private_snippet(client, auth):
    snippet = create(client, auth)

    assert client.get(f"/snippets/{snippet['id']}", headers=auth).status_code == 200


def test_private_snippet_is_hidden_from_others_and_anonymous(client, auth, other_auth):
    snippet = create(client, auth)
    url = f"/snippets/{snippet['id']}"

    assert client.get(url, headers=other_auth).status_code == 404
    assert client.get(url).status_code == 404


def test_public_snippet_is_readable_by_anyone(client, auth):
    snippet = create(client, auth, is_public=True)

    assert client.get(f"/snippets/{snippet['id']}").status_code == 200


def test_get_with_invalid_token_is_unauthorized(client, auth):
    snippet = create(client, auth, is_public=True)
    response = client.get(f"/snippets/{snippet['id']}", headers={"Authorization": "Bearer x"})

    assert response.status_code == 401


def test_get_unknown_snippet(client, auth):
    assert client.get("/snippets/999", headers=auth).status_code == 404


def test_public_listing_excludes_private_and_needs_no_auth(client, auth):
    create(client, auth, title="aberto", is_public=True)
    create(client, auth, title="fechado", is_public=False)

    body = client.get("/public/snippets").json()

    assert [s["title"] for s in body["items"]] == ["aberto"]


def test_public_listing_accepts_filters(client, auth, other_auth):
    create(client, auth, title="a", language="rust", is_public=True)
    create(client, other_auth, title="b", language="python", is_public=True)

    body = client.get("/public/snippets", params={"language": "rust"}).json()

    assert [s["title"] for s in body["items"]] == ["a"]


def test_patch_updates_only_sent_fields(client, auth):
    snippet = create(client, auth)

    response = client.patch(
        f"/snippets/{snippet['id']}", json={"title": "Novo título", "is_public": True}, headers=auth
    )

    body = response.json()
    assert response.status_code == 200
    assert body["title"] == "Novo título"
    assert body["is_public"] is True
    assert body["code"] == snippet["code"]
    assert body["updated_at"] >= snippet["updated_at"]


def test_patch_replaces_tags_and_clears_description(client, auth):
    snippet = create(client, auth, tags=["a", "b"])

    response = client.patch(
        f"/snippets/{snippet['id']}", json={"tags": ["c"], "description": None}, headers=auth
    )

    assert response.json()["tags"] == ["c"]
    assert response.json()["description"] is None


def test_patch_rejects_null_on_required_fields(client, auth):
    snippet = create(client, auth)
    response = client.patch(f"/snippets/{snippet['id']}", json={"title": None}, headers=auth)

    assert response.status_code == 422


def test_patch_by_other_user_on_private_snippet_is_not_found(client, auth, other_auth):
    snippet = create(client, auth)
    response = client.patch(f"/snippets/{snippet['id']}", json={"title": "x"}, headers=other_auth)

    assert response.status_code == 404


def test_patch_by_other_user_on_public_snippet_is_forbidden(client, auth, other_auth):
    snippet = create(client, auth, is_public=True)
    response = client.patch(f"/snippets/{snippet['id']}", json={"title": "x"}, headers=other_auth)

    assert response.status_code == 403


def test_delete_removes_snippet(client, auth):
    snippet = create(client, auth)
    url = f"/snippets/{snippet['id']}"

    assert client.delete(url, headers=auth).status_code == 204
    assert client.get(url, headers=auth).status_code == 404


def test_delete_by_other_user_is_forbidden_for_public(client, auth, other_auth):
    snippet = create(client, auth, is_public=True)
    url = f"/snippets/{snippet['id']}"

    assert client.delete(url, headers=other_auth).status_code == 403
    assert client.get(url).status_code == 200


def test_timestamps_carry_utc_offset_everywhere(client, auth):
    created = create(client, auth)

    fetched = client.get(f"/snippets/{created['id']}", headers=auth).json()
    listed = client.get("/snippets", headers=auth).json()["items"][0]

    for body in (created, fetched, listed):
        assert body["created_at"].endswith("Z")
        assert body["updated_at"].endswith("Z")
