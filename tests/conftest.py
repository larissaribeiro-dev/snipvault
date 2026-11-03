import pytest
from fastapi.testclient import TestClient

from snipvault.config import Settings
from snipvault.main import create_app

PASSWORD = "senha-segura-123"


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        database_url="sqlite://",
        secret_key="chave-de-teste-com-mais-de-trinta-e-dois-caracteres",
    )


@pytest.fixture()
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture()
def login(client):
    """Cria a conta (se ainda não existir) e devolve o header Authorization."""

    def _login(email: str = "ana@example.com") -> dict[str, str]:
        client.post("/auth/register", json={"email": email, "password": PASSWORD})
        response = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login


@pytest.fixture()
def auth(login):
    return login("ana@example.com")


@pytest.fixture()
def other_auth(login):
    return login("bruno@example.com")
