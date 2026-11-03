from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

IN_MEMORY_URLS = {"sqlite://", "sqlite:///:memory:"}


class Base(DeclarativeBase):
    pass


def make_engine(url: str) -> Engine:
    if not url.startswith("sqlite"):
        return create_engine(url, pool_pre_ping=True)

    kwargs: dict[str, object] = {"connect_args": {"check_same_thread": False}}
    if url in IN_MEMORY_URLS:
        # sem isso cada conexão enxergaria um banco vazio diferente
        kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine
