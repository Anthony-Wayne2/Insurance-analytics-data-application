"""
connection_db.py — MySQL connection layer for the Insurance Analytics ETL/API.

Features:
  - SQLAlchemy engine factory with connection pooling
  - Reads credentials from .env via python-dotenv
  - URL-encodes user/password to handle special characters
  - Supports both local MySQL (no SSL) and cloud MySQL (Aiven, SSL)
  - Accepts DB_SSL_CA as either a file path or raw PEM contents
  - Thread-safe singleton engine (double-checked locking)
  - Diagnostic helpers: test_connection(), list_tables()
"""

import os
import sys
import logging
import threading
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Quiet the mysql.connector plugin-registry spam
logging.getLogger("mysql.connector").setLevel(logging.WARNING)


# ------------------------------------------------------------------
# Load .env (looks in the same folder as this script)
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)


# ------------------------------------------------------------------
# Build URL — no query string; SSL handled via connect_args
# ------------------------------------------------------------------
def _build_url() -> str:
    user = os.getenv("DB_USER", "root")
    pwd  = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "insurance_analytics")

    if not pwd:
        raise EnvironmentError(
            f"DB_PASSWORD is empty. Check that {ENV_PATH} exists and contains it, "
            f"or that DB_PASSWORD is set as an environment variable."
        )

    # URL-encode both user and password so special characters (@ : / ? #) are safe
    user_enc = quote_plus(user)
    pwd_enc  = quote_plus(pwd)

    return f"mysql+mysqlconnector://{user_enc}:{pwd_enc}@{host}:{port}/{name}"


# ------------------------------------------------------------------
# Build connect_args — SSL for cloud, no SSL for local
# ------------------------------------------------------------------
def _build_connect_args() -> dict:
    """
    Returns a dict of driver-specific connection arguments.

    Local dev:      DB_SSL unset / 'disabled'  → SSL off
    Aiven / cloud:  DB_SSL=required + DB_SSL_CA=<PEM path or contents>
    """
    ssl_mode = os.getenv("DB_SSL", "disabled").lower()

    if ssl_mode in ("required", "true", "1", "yes"):
        connect_args = {
            "ssl_disabled": False,
            "auth_plugin": "mysql_native_password",
            "ssl_verify_cert": True,
        }

        ca_value = os.getenv("DB_SSL_CA", "").strip()
        if ca_value:
            # Accept EITHER a file path OR the raw PEM contents.
            # Render injects the cert as an environment variable, so the
            # PEM-contents branch is what makes the cloud deployment work.
            if ca_value.startswith("-----BEGIN"):
                connect_args["ssl_ca"] = ca_value
            elif os.path.exists(ca_value):
                connect_args["ssl_ca"] = ca_value
            # else: silently skip — connector may still succeed with system CAs

        logger.info("SSL: enabled (verify_cert=True)")
    else:
        connect_args = {
            "ssl_disabled": True,
            "auth_plugin": "mysql_native_password",
        }
        logger.info("SSL: disabled (local dev)")

    return connect_args


# ------------------------------------------------------------------
# Engine (singleton, thread-safe)
# ------------------------------------------------------------------
_engine: Engine | None = None
_engine_lock = threading.Lock()


def get_engine() -> Engine:
    """
    Return a cached SQLAlchemy engine.
    Thread-safe: concurrent callers block until the first one finishes.
    """
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:                       # double-checked locking
                _engine = create_engine(
                    _build_url(),
                    pool_size=5,
                    max_overflow=10,
                    pool_recycle=3600,
                    pool_pre_ping=True,
                    future=True,
                    echo=False,
                    connect_args=_build_connect_args(),
                )
                logger.info(
                    "Engine created for %s@%s:%s/%s",
                    os.getenv("DB_USER"),
                    os.getenv("DB_HOST"),
                    os.getenv("DB_PORT"),
                    os.getenv("DB_NAME"),
                )
    return _engine


# ------------------------------------------------------------------
# Diagnostics
# ------------------------------------------------------------------
def test_connection() -> bool:
    """Print a short report. Raise on failure."""
    try:
        with get_engine().connect() as conn:
            version = conn.execute(text("SELECT VERSION();")).scalar()
            db_name = conn.execute(text("SELECT DATABASE();")).scalar()
        print()
        print("=" * 55)
        print(f"  Connected to MySQL {version}")
        print(f"  Active database   : {db_name}")
        print("=" * 55)
        return True
    except SQLAlchemyError as e:
        print()
        print("=" * 55)
        print("  CONNECTION FAILED")
        print("=" * 55)
        print(f"  {type(e).__name__}: {e}")
        print()
        print("  Common fixes:")
        print("   - Is MySQL running?  (sc query MySQL267)")
        print("   - Are DB_* env vars set correctly?")
        print("   - For Aiven: DB_SSL=required + DB_SSL_CA=<PEM>")
        print("   - Is the DB user password correct?")
        print()
        return False


def list_tables() -> None:
    sql = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        ORDER BY table_name;
    """)
    with get_engine().connect() as conn:
        rows = [r[0] for r in conn.execute(sql)]
    print()
    print(f"Tables in {os.getenv('DB_NAME')}: {len(rows)}")
    for t in rows:
        print(f"   - {t}")


# ------------------------------------------------------------------
# ENTRY POINT — self-test when run directly
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("Running MySQL connection diagnostics...")
    ok = test_connection()
    if not ok:
        sys.exit(1)
    list_tables()
    print("\nAll good. You can now run etl_pipeline.py or the API.\n")
