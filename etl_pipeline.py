"""
ETL Pipeline: CSV -> insurance_analytics (MySQL)
------------------------------------------------
Extract from four CSVs, profile missing values, apply the 60% rule,
enforce referential integrity, load into MySQL, and log every decision.

Missing-value rule (per column):
    - % missing  > 60%     -> DROP the column
    - 0 < % missing <= 60% -> IMPUTE
         numeric   : grouped median (fallback global median)
         datetime  : median date
         text      : mode (fallback 'Unknown')
    - PK / FK columns are NEVER imputed -> rows with null keys are dropped.

Uses connection_db.get_engine() for the database connection.
"""

import os
import sys
import numpy as np
import pandas as pd
from sqlalchemy import text

from connection_db import get_engine, create_schema


# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
DATA_DIR = "data"
FILES = {
    "patients":  "patients.csv",
    "providers": "providers.csv",
    "claims":    "claims.csv",
    "payments":  "payments.csv",
}

MISSING_THRESHOLD = 0.60          # 60 %
PRIMARY_KEYS = {
    "patients":  "patient_id",
    "providers": "provider_id",
    "claims":    "claim_id",
    "payments":  "payment_id",
}
FOREIGN_KEYS = {
    "claims":   ["patient_id", "provider_id"],
    "payments": ["claim_id"],
}


# ------------------------------------------------------------------
# EXTRACT
# ------------------------------------------------------------------
def extract(file_name: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing input file: {path}")
    df = pd.read_csv(path)
    print(f"[EXTRACT] {file_name}: {df.shape[0]} rows x {df.shape[1]} cols")
    return df


# ------------------------------------------------------------------
# PROFILING
# ------------------------------------------------------------------
def profile_missing(df: pd.DataFrame, name: str) -> pd.DataFrame:
    """Print % missing per column (desc). Return as a dataframe."""
    pct = (df.isna().mean() * 100).round(2).sort_values(ascending=False)
    report = pct.reset_index()
    report.columns = ["column", "pct_missing"]
    print(f"\n===== MISSING-VALUE PROFILE: {name} =====")
    if report.empty:
        print("  (no columns)")
    else:
        print(report.to_string(index=False))
    return report


# ------------------------------------------------------------------
# COMMON CLEANING
# ------------------------------------------------------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.str.strip()
                  .str.lower()
                  .str.replace(r"[^\w]+", "_", regex=True)
                  .str.strip("_")
    )
    return df


def strip_strings(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include="object").columns:
        df[col] = (
            df[col].astype(str)
                    .str.strip()
                    .replace({"nan": np.nan, "": np.nan, "None": np.nan,
                              "NaN": np.nan, "NULL": np.nan})
        )
    return df


# ------------------------------------------------------------------
# MISSING-VALUE HANDLER (60 % RULE)
# ------------------------------------------------------------------
def handle_missing(df: pd.DataFrame,
                   name: str,
                   group_col: str = None,
                   protected_cols: list = None) -> tuple:
    """
    Apply 60% rule per column:
      > 60% missing   -> drop column
      <= 60% missing  -> impute (median / mode)
    Protected cols (PK/FK) are untouched here — nulls dropped later.
    Returns (df, decisions_list).
    """
    protected_cols = set(protected_cols or [])
    decisions = []
    n_rows = len(df)

    for col in list(df.columns):
        pct_missing = float(df[col].isna().mean())   # plain Python float

        # --- PK/FK protection ---
        if col in protected_cols:
            decisions.append({
                "table": name, "column": col,
                "pct_missing": round(pct_missing * 100, 2),
                "action": "PROTECTED",
                "method": "PK/FK - rows dropped later if null",
            })
            continue

        # --- RULE 1: drop if > 60% missing ---
        if pct_missing > MISSING_THRESHOLD:
            df = df.drop(columns=[col])
            print(f"  [{name}] DROP   '{col}'  ({pct_missing:.1%} missing)")
            decisions.append({
                "table": name, "column": col,
                "pct_missing": round(pct_missing * 100, 2),
                "action": "DROPPED",
                "method": f">{int(MISSING_THRESHOLD * 100)}% missing",
            })
            continue

        # --- nothing missing ---
        if pct_missing == 0:
            decisions.append({
                "table": name, "column": col,
                "pct_missing": 0.0,
                "action": "OK",
                "method": "no missing",
            })
            continue

        # --- RULE 2: impute (<= 60% missing) ---
        if pd.api.types.is_numeric_dtype(df[col]):
            if group_col and group_col in df.columns and \
               not pd.api.types.is_numeric_dtype(df[group_col]):
                df[col] = df.groupby(group_col)[col].transform(
                    lambda s: s.fillna(s.median())
                )
                df[col] = df[col].fillna(df[col].median())   # fallback
                method = f"grouped median by '{group_col}'"
            else:
                df[col] = df[col].fillna(df[col].median())
                method = "global median"

        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
            method = "median date"

        else:  # text / categorical
            mode_series = df[col].mode(dropna=True)
            fill_val = mode_series.iloc[0] if not mode_series.empty else "Unknown"
            df[col] = df[col].fillna(fill_val)
            method = f"mode ('{fill_val}')"

        print(f"  [{name}] IMPUTE '{col}'  ({pct_missing:.1%} missing) -> {method}")
        decisions.append({
            "table": name, "column": col,
            "pct_missing": round(pct_missing * 100, 2),
            "action": "IMPUTED",
            "method": method,
        })

    print(f"  [{name}] rows before={n_rows}, after={len(df)}, "
          f"cols={df.shape[1]}")
    return df, decisions


# ------------------------------------------------------------------
# TABLE-SPECIFIC CLEANERS
# ------------------------------------------------------------------
def clean_patients(df: pd.DataFrame) -> tuple:
    df = normalize_columns(df)
    df = strip_strings(df)

    # PK present -> drop duplicate & null
    if "patient_id" in df.columns:
        df = df.drop_duplicates(subset=["patient_id"])

    # Coerce numeric/date-like columns
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
    if "zip_code" in df.columns:
        df["zip_code"] = df["zip_code"].astype(str)

    df, decisions = handle_missing(
        df, "patients",
        group_col="state",
        protected_cols=["patient_id"],
    )

    # Critical: PK must exist
    df = df.dropna(subset=["patient_id"])

    # Sensible defaults for standard fields (only if the column survived)
    if "gender" in df.columns:
        df["gender"] = df["gender"].fillna("Unknown").astype(str).str.title()

    return df, decisions


def clean_providers(df: pd.DataFrame) -> tuple:
    df = normalize_columns(df)
    df = strip_strings(df)

    if "provider_id" in df.columns:
        df = df.drop_duplicates(subset=["provider_id"])

    if "zip_code" in df.columns:
        df["zip_code"] = df["zip_code"].astype(str)

    df, decisions = handle_missing(
        df, "providers",
        group_col="state",
        protected_cols=["provider_id"],
    )
    df = df.dropna(subset=["provider_id"])
    return df, decisions


def clean_claims(df: pd.DataFrame,
                 valid_patients: set,
                 valid_providers: set) -> tuple:
    df = normalize_columns(df)
    df = strip_strings(df)

    if "claim_id" in df.columns:
        df = df.drop_duplicates(subset=["claim_id"])

    if "claim_date" in df.columns:
        df["claim_date"] = pd.to_datetime(df["claim_date"], errors="coerce")
    if "claim_amount" in df.columns:
        df["claim_amount"] = pd.to_numeric(df["claim_amount"], errors="coerce")

    df, decisions = handle_missing(
        df, "claims",
        group_col="status",
        protected_cols=["claim_id", "patient_id", "provider_id"],
    )

    # Critical columns must exist
    df = df.dropna(subset=["claim_id", "patient_id", "provider_id"])

    if "claim_amount" in df.columns:
        df["claim_amount"] = df["claim_amount"].abs().round(2)
        df = df.dropna(subset=["claim_amount"])

    if "status" in df.columns:
        df["status"] = df["status"].fillna("Pending").astype(str).str.title()

    # Referential integrity
    df = df[df["patient_id"].isin(valid_patients)]
    df = df[df["provider_id"].isin(valid_providers)]
    return df, decisions


def clean_payments(df: pd.DataFrame, valid_claims: set) -> tuple:
    df = normalize_columns(df)
    df = strip_strings(df)

    if "payment_id" in df.columns:
        df = df.drop_duplicates(subset=["payment_id"])

    for col in ("payment_date", "claim_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ("payment_amount", "claim_amount"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df, decisions = handle_missing(
        df, "payments",
        group_col="status",
        protected_cols=["payment_id", "claim_id"],
    )

    df = df.dropna(subset=["payment_id", "claim_id"])
    if "payment_amount" in df.columns:
        df["payment_amount"] = df["payment_amount"].abs().round(2)
        df = df.dropna(subset=["payment_amount"])

    df = df[df["claim_id"].isin(valid_claims)]
    return df, decisions


# ------------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------------
def validate(df: pd.DataFrame, name: str) -> None:
    print(f"\n[VALIDATE] {name}  rows={len(df)}  cols={df.shape[1]}")
    print("  remaining nulls :", int(df.isna().sum().sum()))
    print("  duplicate rows  :", int(df.duplicated().sum()))


# ------------------------------------------------------------------
# AUDIT
# ------------------------------------------------------------------
AUDIT_DDL = """
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


def write_audit(engine, decisions: list) -> None:
    """Insert all decisions into etl_missing_value_audit."""
    if not decisions:
        print("[AUDIT] no decisions to log")
        return

    # Normalize numeric types so the driver never sees np.float64
    clean = [{
        "table":       str(d.get("table", ""))[:50],
        "column":      str(d.get("column", ""))[:50],
        "pct_missing": float(d.get("pct_missing", 0.0)),
        "action":      str(d.get("action", ""))[:20],
        "method":      str(d.get("method", ""))[:120],
    } for d in decisions]

    with engine.begin() as conn:
        conn.execute(text(AUDIT_DDL))
        conn.execute(
            text("""
                INSERT INTO etl_missing_value_audit
                    (table_name, column_name, pct_missing, action, method)
                VALUES (:table, :column, :pct_missing, :action, :method)
            """),
            clean,
        )
    print(f"[AUDIT] {len(clean)} decisions logged")


# ------------------------------------------------------------------
# LOAD
# ------------------------------------------------------------------
def load(df: pd.DataFrame, table: str, engine) -> None:
    if df.empty:
        print(f"[LOAD] {table}: 0 rows (skipped)")
        return
    df.to_sql(
        table,
        con=engine,
        if_exists="append",
        index=False,
        method="multi",       # fast batched INSERT
        chunksize=1000,
    )
    print(f"[LOAD] {table}: {len(df)} rows inserted")


def truncate_targets(engine) -> None:
    """Clear target tables before reload (children first)."""
    order = ["payments", "claims", "providers", "patients",
             "etl_missing_value_audit"]
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        for t in order:
            conn.execute(text(f"TRUNCATE TABLE {t};"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    print(f"[CLEAN] Truncated {len(order)} target tables")


# ------------------------------------------------------------------
# ORCHESTRATION
# ------------------------------------------------------------------
def main():
    print("=" * 60)
    print("Insurance Analytics ETL — starting")
    print("=" * 60)

    # 0. DB setup (idempotent)
    create_schema()
    engine = get_engine()
    truncate_targets(engine)          # fresh reload each run

    # 1. EXTRACT
    print("\n===== EXTRACT =====")
    raw = {name: extract(fname) for name, fname in FILES.items()}

    # 2. PROFILE
    print("\n===== PROFILE (before cleaning) =====")
    for name, df in raw.items():
        profile_missing(df, name)

    # 3. TRANSFORM
    print("\n===== TRANSFORM =====")
    patients,  d1 = clean_patients(raw["patients"])
    providers, d2 = clean_providers(raw["providers"])
    claims,    d3 = clean_claims(
        raw["claims"],
        valid_patients=set(patients["patient_id"]),
        valid_providers=set(providers["provider_id"]),
    )
    payments,  d4 = clean_payments(
        raw["payments"],
        valid_claims=set(claims["claim_id"]),
    )
    all_decisions = d1 + d2 + d3 + d4

    # 4. VALIDATE
    print("\n===== VALIDATE =====")
    for name, df in [("patients", patients), ("providers", providers),
                     ("claims", claims), ("payments", payments)]:
        validate(df, name)

    # 5. LOAD — parents first, then children (FK order)
    print("\n===== LOAD =====")
    load(patients,  "patients",  engine)
    load(providers, "providers", engine)
    load(claims,    "claims",    engine)
    load(payments,  "payments",  engine)

    # 6. AUDIT
    print("\n===== AUDIT =====")
    write_audit(engine, all_decisions)

    print("\n" + "=" * 60)
    print("[OK] ETL pipeline completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FAIL] ETL aborted: {type(e).__name__}: {e}")
        sys.exit(1)
