import logging
import os
from pathlib import Path

from rich.logging import RichHandler
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base
from utils.settings import get_settings

logging.basicConfig(level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
logger = logging.getLogger(__name__)


def init_db(override: bool = False):
    db_path = get_settings().get("db_path", "")
    db_file = Path(db_path.replace("sqlite:", "", 1))
    logger.debug(f"Database path is: {db_file}")
    if db_file.exists():
        if override:
            db_file.unlink()
            logger.info("Existing database deleted (override=True).")
        else:
            logger.info("Database already exists. Use --override to delete and recreate.")
            return

    if not db_file.parent.exists():
        db_file.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(db_path, echo=False)
    Base.metadata.create_all(engine)

    set_permissions(db_file)

    logger.info("Database initialized.")


def get_session() -> "Session":
    db_path = get_settings().get("db_path", "")
    engine = create_engine(db_path, echo=False)
    session = sessionmaker(bind=engine)
    return session()


def set_permissions(db_file: Path) -> None:
    # Set database file permissions to 664 (rw-rw-r--)
    try:
        os.chmod(db_file, 0o664)
        logger.debug(f"Set database file permissions to 664: {db_file}")
    except OSError as e:
        logger.warning(f"Failed to set database file permissions: {e}")

    # Set folder permissions to 775 (rwxrwxr-x) for directory traversal
    try:
        os.chmod(db_file.parent, 0o775)
        logger.debug(f"Set database folder permissions to 775: {db_file.parent}")
    except OSError as e:
        logger.warning(f"Failed to set database folder permissions: {e}")
