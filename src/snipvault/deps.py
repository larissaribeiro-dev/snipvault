from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from snipvault.config import Settings
from snipvault.models import User
from snipvault.security import decode_access_token
from snipvault.services.snippets import SnippetFilters

bearer_scheme = HTTPBearer(auto_error=False)


def get_db(request: Request) -> Iterator[Session]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_optional_user(
    credentials: Credentials, db: DbSession, settings: AppSettings
) -> User | None:
    if credentials is None:
        return None
    user_id = decode_access_token(credentials.credentials, settings)
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise _unauthorized("Token inválido ou expirado")
    return user


def get_current_user(user: Annotated[User | None, Depends(get_optional_user)]) -> User:
    if user is None:
        raise _unauthorized("Autenticação necessária")
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@dataclass(frozen=True)
class Listing:
    filters: SnippetFilters
    limit: int
    offset: int


def get_listing(
    q: Annotated[
        str | None, Query(max_length=100, description="Busca em título, descrição e código")
    ] = None,
    language: Annotated[str | None, Query(max_length=30)] = None,
    tag: Annotated[str | None, Query(max_length=30)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Listing:
    return Listing(SnippetFilters(q=q, language=language, tag=tag), limit, offset)


ListingParams = Annotated[Listing, Depends(get_listing)]
