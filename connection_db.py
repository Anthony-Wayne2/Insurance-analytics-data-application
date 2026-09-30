"""
connection_db.py — MySQL connection layer for the Insurance Analytics ETL.
Running this file directly will test the connection and create the schema.
"""

import os
import sys
import logging
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


# ------------------------------------------------------------------
# Load .env
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)


# ------------------------------------------------------------------
# Build URL — URL-encode user & password so special chars are safe
# ------------------------------------------------------------------
def _build_url() -> str:
    user = os.getenv("DB_USER", "root")
    pwd  = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "insurance_analytics")

    if not pwd:
        raise EnvironmentError(
            f"DB_PASSWORD is empty. Check that {ENV_PATH} exists and contains it."
        )

    user_enc = quote_plus(user)
    pwd_enc  = quote_plus(pwd)

    return f"mysql+mysqlconnector://{user_enc}:{pwd_enc}@{host}:{port}/{name}"


# ------------------------------------------------------------------
# Engine (singleton)
# ------------------------------------------------------------------
_engine: Engine | None = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = _build_url()
        # Mask the password when logging
        safe_url = url.split("@")[-1] if "@" in url else url
        logger.info("Engine created for %s@%s/%s",
                    os.getenv("DB_USER"), os.getenv("DB_HOST"),
                    os.getenv("DB_NAME"))
        _engine = create_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            pool_pre_ping=True,
            future=True,
            echo=False,
            connect_args={
                # Local dev only — remove for remote/cloud DBs
                "ssl_disabled": True,
		"auth_plugin": "mysql_native_password",
            },
        )
    return _engine


# ------------------------------------------------------------------
# Test connection
# ------------------------------------------------------------------
def test_connection() -> bool:
    try:
        with get_engine().connect() as conn:
            version = conn.execute(text("SELECT VERSION();")).scalar()
            db_name = conn.execute(text("SELECT DATABASE();")).scalar()
        print()
        print("=" * 55)
        print(f"Connected to MySQL {version}")
        print(f"Active database   : {db_name}")
        print("=" * 55)
        return True
    except SQLAlchemyError as e:
        print()
        print("=" * 55)
        print("CONNECTION FAILED")
        print("=" * 55)
        print(f"  {type(e).__name__}: {e}")
        print()
        print("  Common fixes:")
        print("   • Is MySQL running?  (Get-Service MySQL80)")
        print("   • Does .env exist with DB_USER / DB_PASSWORD?")
        print("   • Is the DB created? (CREATE DATABASE insurance_analytics;)")
        print("   • Correct root password in .env?")
        print()
        return False


# ------------------------------------------------------------------
# Schema DDL
# ------------------------------------------------------------------
SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS patients (
    patient_id      VARCHAR(20) PRIMARY KEY,
    first_name      VARCHAR(50),
    last_name       VARCHAR(50),
    gender          VARCHAR(10),
    dob             DATE,
    phone           VARCHAR(20),
    city            VARCHAR(50),
    state           VARCHAR(20),
    insurance_plan  VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS providers (
    provider_id     VARCHAR(20) PRIMARY KEY,
    provider_name   VARCHAR(100),
    specialty       VARCHAR(60),
    hospital        VARCHAR(100),
    city            VARCHAR(50),
    state           VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id        VARCHAR(20) PRIMARY KEY,
    patient_id      VARCHAR(20),
    provider_id     VARCHAR(20),
    claim_date      DATE,
    diagnosis_code  VARCHAR(20),
    claim_amount    DECIMAL(12,2),
    status          VARCHAR(20),
    FOREIGN KEY (patient_id)  REFERENCES patients(patient_id),
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id      VARCHAR(20) PRIMARY KEY,
    claim_id        VARCHAR(20),
    payment_date    DATE,
    paid_amount     DECIMAL(12,2),
    payment_method  VARCHAR(30),
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
);

CREATE TABLE IF NOT EXISTS etl_missing_value_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name   VARCHAR(50),
    column_name  VARCHAR(50),
    pct_missing  DECIMAL(6,2),
    action       VARCHAR(20),
    method       VARCHAR(120),
    run_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def create_schema() -> None:
    engine = get_engine()
    stmts = [s.strip() for s in SCHEMA_DDL.split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in stmts:
            conn.execute(text(stmt))
    logger.info("Schema ready (%d statements executed)", len(stmts))


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
    print(f" Tables in {os.getenv('DB_NAME')}: {len(rows)}")
    for t in rows:
        print(f"   • {t}")


# ------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("Running MySQL connection diagnostics...")
    ok = test_connection()
    if not ok:
        sys.exit(1)
    create_schema()
    list_tables()
    print("\n All good. You can now run etl_pipeline.py\n")
    