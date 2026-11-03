import jwt

from snipvault import security
from snipvault.config import Settings


def make_settings(**overrides) -> Settings:
    base = {"secret_key": "chave-de-teste-com-mais-de-trinta-e-dois-caracteres"}
    return Settings(**{**base, **overrides})


def test_hash_is_salted():
    assert security.hash_password("abc12345") != security.hash_password("abc12345")


def test_verify_password():
    stored = security.hash_password("abc12345")

    assert security.verify_password("abc12345", stored)
    assert not security.verify_password("outra-senha", stored)


def test_verify_password_rejects_malformed_hash():
    assert not security.verify_password("abc12345", "isso-nao-e-um-hash")
    assert not security.verify_password("abc12345", "bcrypt$1$2$3$aa$bb")


def test_token_roundtrip():
    settings = make_settings()
    token = security.create_access_token(42, settings)

    assert security.decode_access_token(token, settings) == 42


def test_expired_token_is_rejected():
    settings = make_settings(access_token_minutes=-1)
    token = security.create_access_token(42, settings)

    assert security.decode_access_token(token, settings) is None


def test_token_signed_with_another_key_is_rejected():
    token = security.create_access_token(42, make_settings())
    other = make_settings(secret_key="outra-chave-igualmente-longa-para-o-teste-0000")

    assert security.decode_access_token(token, other) is None


def test_token_without_subject_is_rejected():
    settings = make_settings()
    token = jwt.encode({"exp": 9999999999}, settings.secret_key, algorithm=settings.algorithm)

    assert security.decode_access_token(token, settings) is None
