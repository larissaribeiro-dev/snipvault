import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import sessionmaker

from snipvault import __version__
from snipvault.config import DEFAULT_SECRET_KEY, Settings, get_settings
from snipvault.database import Base, make_engine
from snipvault.errors import DomainError
from snipvault.routers import auth, health, snippets

logger = logging.getLogger("snipvault")

DESCRIPTION = """
API para guardar, buscar e compartilhar trechos de código.

Crie uma conta em `/auth/register`, pegue um token em `/auth/login` e use o botão
**Authorize** para testar as rotas protegidas por aqui.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    if settings.secret_key == DEFAULT_SECRET_KEY:
        logger.warning("SNIPVAULT_SECRET_KEY está com o valor padrão. Troque antes de publicar.")

    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(
        title="snipvault",
        version=__version__,
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(snippets.router)
    app.include_router(snippets.public_router)
    return app
