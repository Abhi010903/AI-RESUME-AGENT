"""SQLAlchemy database engine, session management, and connectivity checks."""

from collections.abc import Generator
import logging
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.config import Settings, get_settings

logger = logging.getLogger("app.database")


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""

    pass


_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


def get_engine(settings: Settings | None = None) -> Engine:
    """Create or return the cached SQLAlchemy Engine."""
    global _engine, _SessionFactory
    if _engine is None:
        cfg = settings or get_settings()
        connect_args: dict[str, object] = {}

        # SQLite requires check_same_thread=False for multi-threaded FastAPI workers
        if cfg.is_sqlite:
            connect_args["check_same_thread"] = False

        engine_kwargs: dict[str, object] = {
            "connect_args": connect_args,
            "pool_pre_ping": True,
            "echo": cfg.debug,
        }

        # In-memory SQLite requires StaticPool so connections share the same memory DB
        if cfg.is_sqlite and ":memory:" in cfg.database_url:
            from sqlalchemy.pool import StaticPool

            engine_kwargs["poolclass"] = StaticPool

        _engine = create_engine(cfg.database_url, **engine_kwargs)
        _SessionFactory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
        )
        # Safely render URL with password masked to prevent credential exposure in logs
        safe_url = _engine.url.render_as_string(hide_password=True)
        logger.info("Database engine initialized", extra={"url": safe_url})
    return _engine


def get_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    """Return configured session factory."""
    global _SessionFactory
    if _SessionFactory is None:
        get_engine(settings)
    assert _SessionFactory is not None
    return _SessionFactory


def init_db(engine: Engine | None = None) -> None:
    """Initialize database tables using metadata."""
    import app.models  # noqa: F401 - ensure models register with Base.metadata
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
    logger.info("Database schema initialized")


def close_db_engine() -> None:
    """Dispose the engine connection pool gracefully."""
    global _engine, _SessionFactory
    if _engine is not None:
        try:
            _engine.dispose()
            logger.info("Database engine disposed")
        except Exception as exc:
            logger.error("Error disposing database engine: %s", exc)
        finally:
            _engine = None
            _SessionFactory = None


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session per request."""
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_health(engine: Engine | None = None) -> tuple[bool, str | None]:
    """Perform a live check against the database with a lightweight SELECT 1 query."""
    eng = engine or get_engine()
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return False, str(exc)
