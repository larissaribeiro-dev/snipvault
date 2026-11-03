from tests.conftest import PASSWORD


def register(client, email="ana@example.com", password=PASSWORD):
    return client.post("/auth/register", json={"email": email, "password": password})


def test_register_returns_user_without_password(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@example.com"
    assert "password" not in body and "password_hash" not in body


def test_register_normalizes_email(client):
    response = register(client, email="  Ana@Example.COM ")

    assert response.json()["email"] == "ana@example.com"


def test_register_duplicate_email_returns_conflict(client):
    register(client)
    response = register(client, email="ANA@example.com")

    assert response.status_code == 409


def test_register_rejects_invalid_email(client):
    assert register(client, email="nao-e-email").status_code == 422


def test_register_rejects_short_password(client):
    assert register(client, password="curta").status_code == 422


def test_login_returns_bearer_token(client):
    register(client)
    response = client.post("/auth/login", json={"email": "ana@example.com", "password": PASSWORD})

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_with_wrong_password(client):
    register(client)
    response = client.post(
        "/auth/login", json={"email": "ana@example.com", "password": "errada123"}
    )

    assert response.status_code == 401


def test_login_with_unknown_email(client):
    response = client.post("/auth/login", json={"email": "ninguem@example.com", "password": "x"})

    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_returns_current_user(client, auth):
    response = client.get("/auth/me", headers=auth)

    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"


def test_me_rejects_garbage_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer lixo"})

    assert response.status_code == 401
