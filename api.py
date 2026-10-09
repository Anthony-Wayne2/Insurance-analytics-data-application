"""
api.py — Insurance Analytics Dashboard API
==========================================
FastAPI backend serving all KPIs as JSON endpoints.

Features:
  - Verified SQL from analytics_queries.sql
  - In-memory TTL cache (60s default) to keep the dashboard < 3s
  - CORS configurable via CORS_ORIGINS env var (comma-separated)
  - Automatic OpenAPI docs at /docs
  - /api/health for liveness + DB connectivity check
  - /metrics stub to silence monitoring probes
"""

import hashlib
import json
import os
import time
from datetime import date
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from connection_db import get_engine
import traceback
import logging

logger = logging.getLogger("uvicorn.error")

# ==================================================================
# APP SETUP
# ==================================================================
app = FastAPI(
    title="Insurance Analytics API",
    version="1.0.0",
    description="JSON API powering the Insurance Analytics Dashboard",
)


# ==================================================================
# CORS — configurable via env var, with sensible local defaults
# ==================================================================
_cors_default = (
    "http://localhost:5173,"
    "http://localhost:4173,"
    "http://127.0.0.1:5173,"
    "http://127.0.0.1:4173"
)

cors_origins = [
    o.strip().rstrip("/")
    for o in os.getenv("CORS_ORIGINS", _cors_default).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Print the actual origins at boot for debugging
print("=" * 60, flush=True)
print(f"CORS origins loaded: {cors_origins}", flush=True)
print("=" * 60, flush=True)

# ==================================================================
# CACHE — simple in-memory TTL cache
# ==================================================================
_cache: dict = {}
CACHE_TTL = 60          # seconds


def _cache_key(sql: str, params: dict) -> str:
    raw = sql + json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def _run_query(sql: str, params: dict, ttl: int = CACHE_TTL) -> list[dict]:
    """
    Execute SQL, cache the result for `ttl` seconds.
    Returns a list of JSON-friendly dicts.
    """
    key = _cache_key(sql, params)
    now = time.time()

    if key in _cache and (now - _cache[key]["t"]) < ttl:
        return _cache[key]["v"]

    engine = get_engine()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params=params)
        # Convert NaN to None and strip numpy scalar types
        df = df.where(pd.notnull(df), None)
        result = json.loads(json.dumps(df.to_dict(orient="records"), default=str))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

    _cache[key] = {"v": result, "t": now}
    return result


def _date_params(start_date: Optional[date], end_date: Optional[date]) -> dict:
    return {
        "start_date": start_date.isoformat() if start_date else None,
        "end_date":   end_date.isoformat()   if end_date   else None,
    }


# ==================================================================
# HEALTH + ADMIN
# ==================================================================
@app.get("/", tags=["health"])
def root():
    return {"service": "Insurance Analytics API", "status": "ok"}


@app.get("/api/health", tags=["health"])
def health():
    """Liveness + DB connectivity check with full error logging."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"db": "ok"}
    except Exception as e:
        # Print full traceback to stdout for Render's log panel
        print("=" * 60, flush=True)
        print("HEALTH CHECK FAILED", flush=True)
        print("=" * 60, flush=True)
        traceback.print_exc()
        print("=" * 60, flush=True)
        raise HTTPException(
            status_code=503,
            detail=f"DB unavailable: {type(e).__name__}: {e}"
        )


@app.get("/metrics", include_in_schema=False)
def metrics_stub():
    """Silences common monitoring probes looking for Prometheus metrics."""
    return {"note": "no metrics collector configured"}


@app.get("/api/cache/clear", tags=["admin"])
def cache_clear():
    n = len(_cache)
    _cache.clear()
    return {"cleared": n}


@app.get("/api/cache/stats", tags=["admin"])
def cache_stats():
    return {
        "size": len(_cache),
        "ttl_seconds": CACHE_TTL,
        "keys": list(_cache.keys())[:10],
    }


# ==================================================================
# KPI 1, 2, 6 — Claims headline
# ==================================================================
@app.get("/api/kpis/claims", tags=["kpis"])
def kpi_claims(
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
):
    sql = """
        SELECT
          COUNT(DISTINCT claim_id)        AS total_claims,
          COALESCE(SUM(claim_amount), 0)  AS total_claimed,
          COALESCE(AVG(claim_amount), 0)  AS avg_claim_amount
        FROM claims
        WHERE (:start_date IS NULL OR claim_date >= :start_date)
          AND (:end_date   IS NULL OR claim_date <= :end_date)
    """
    rows = _run_query(sql, _date_params(start_date, end_date))
    return rows[0] if rows else {}


# ==================================================================
# KPI 3, 4, 22 — Payments headline + payment ratio
# ==================================================================
@app.get("/api/kpis/payments", tags=["kpis"])
def kpi_payments(
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
):
    paid_sql = """
        SELECT
          COALESCE(SUM(payment_amount), 0) AS total_paid,
          COALESCE(AVG(payment_amount), 0) AS avg_payment_amount
        FROM payments
        WHERE (:start_date IS NULL OR payment_date >= :start_date)
          AND (:end_date   IS NULL OR payment_date <= :end_date)
    """
    claimed_sql = """
        SELECT COALESCE(SUM(claim_amount), 0) AS total_claimed
        FROM claims
        WHERE (:start_date IS NULL OR claim_date >= :start_date)
          AND (:end_date   IS NULL OR claim_date <= :end_date)
    """
    p = _date_params(start_date, end_date)
    paid = _run_query(paid_sql, p)[0]
    claimed = _run_query(claimed_sql, p)[0]

    total_claimed = claimed["total_claimed"] or 0
    total_paid = paid["total_paid"] or 0
    ratio = round((total_paid / total_claimed * 100), 2) if total_claimed else 0

    return {
        "total_paid": paid["total_paid"],
        "avg_payment_amount": paid["avg_payment_amount"],
        "payment_ratio": ratio,
    }


# ==================================================================
# KPI 5 — Monthly claim volume
# ==================================================================
@app.get("/api/charts/monthly-claims", tags=["charts"])
def chart_monthly_claims(
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
):
    sql = """
        SELECT
          DATE_FORMAT(claim_date, '%Y-%m') AS month,
          COUNT(*)                         AS claims,
          COALESCE(SUM(claim_amount), 0)   AS claimed_value
        FROM claims
        WHERE (:start_date IS NULL OR claim_date >= :start_date)
          AND (:end_date   IS NULL OR claim_date <= :end_date)
        GROUP BY month
        ORDER BY month
    """
    return _run_query(sql, _date_params(start_date, end_date))


# ==================================================================
# KPI 7 — Month-over-month growth
# ==================================================================
@app.get("/api/charts/mom-growth", tags=["charts"])
def chart_mom_growth():
    sql = """
        SELECT
          month,
          claims,
          LAG(claims) OVER (ORDER BY month) AS prev_month_claims,
          ROUND(
            (claims - LAG(claims) OVER (ORDER BY month))
            / NULLIF(LAG(claims) OVER (ORDER BY month), 0) * 100, 2
          ) AS mom_growth_pct
        FROM (
          SELECT DATE_FORMAT(claim_date, '%Y-%m') AS month, COUNT(*) AS claims
          FROM claims
          GROUP BY month
        ) t
        ORDER BY month
    """
    return _run_query(sql, {})


# ==================================================================
# KPI 8 — Claims by status
# ==================================================================
@app.get("/api/charts/status", tags=["charts"])
def chart_status(
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
):
    sql = """
        SELECT
          status,
          COUNT(*)                       AS n,
          COALESCE(SUM(claim_amount), 0) AS value
        FROM claims
        WHERE (:start_date IS NULL OR claim_date >= :start_date)
          AND (:end_date   IS NULL OR claim_date <= :end_date)
        GROUP BY status
        ORDER BY n DESC
    """
    return _run_query(sql, _date_params(start_date, end_date))


# ==================================================================
# KPI 9, 25 — Approval & rejection rates
# ==================================================================
@app.get("/api/kpis/rates", tags=["kpis"])
def kpi_rates(
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
):
    sql = """
        SELECT
          ROUND(SUM(status = 'Approved') / NULLIF(COUNT(*), 0) * 100, 2) AS approval_rate,
          ROUND(SUM(status = 'Rejected') / NULLIF(COUNT(*), 0) * 100, 2) AS rejection_rate,
          ROUND(SUM(status = 'Pending')  / NULLIF(COUNT(*), 0) * 100, 2) AS pending_rate
        FROM claims
        WHERE (:start_date IS NULL OR claim_date >= :start_date)
          AND (:end_date   IS NULL OR claim_date <= :end_date)
    """
    rows = _run_query(sql, _date_params(start_date, end_date))
    return rows[0] if rows else {}


# ==================================================================
# KPI 10 — Pending claims value
# ==================================================================
@app.get("/api/kpis/pending", tags=["kpis"])
def kpi_pending():
    sql = """
        SELECT
          COUNT(*)                       AS pending_count,
          COALESCE(SUM(claim_amount), 0) AS pending_value
        FROM claims
        WHERE status = 'Pending'
    """
    rows = _run_query(sql, {})
    return rows[0] if rows else {}


# ==================================================================
# KPI 11 — Top providers
# ==================================================================
@app.get("/api/charts/top-providers", tags=["charts"])
def chart_top_providers(
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
    state:      Optional[str]  = Query(None),
    limit:      int            = Query(10, ge=1, le=50),
):
    sql = f"""
        SELECT
          p.provider_id,
          p.name                           AS provider_name,
          p.specialty,
          p.state,
          COUNT(*)                         AS claim_count,
          COALESCE(SUM(c.claim_amount), 0) AS total_claimed
        FROM claims c
        JOIN providers p ON c.provider_id = p.provider_id
        WHERE (:start_date IS NULL OR c.claim_date >= :start_date)
          AND (:end_date   IS NULL OR c.claim_date <= :end_date)
          AND (:state      IS NULL OR p.state = :state)
        GROUP BY p.provider_id, p.name, p.specialty, p.state
        ORDER BY total_claimed DESC
        LIMIT {int(limit)}
    """
    params = _date_params(start_date, end_date)
    params["state"] = state
    return _run_query(sql, params)


# ==================================================================
# KPI 12 — Claims by specialty (filter-aware)
# ==================================================================
@app.get("/api/charts/specialty", tags=["charts"])
def chart_specialty(
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
):
    sql = """
        SELECT
          p.specialty,
          COUNT(*)                         AS claim_count,
          COALESCE(SUM(c.claim_amount), 0) AS total_claimed,
          ROUND(COALESCE(AVG(c.claim_amount), 0), 2) AS avg_claim_amount
        FROM claims c
        JOIN providers p ON c.provider_id = p.provider_id
        WHERE (:start_date IS NULL OR c.claim_date >= :start_date)
          AND (:end_date   IS NULL OR c.claim_date <= :end_date)
        GROUP BY p.specialty
        ORDER BY claim_count DESC
    """
    return _run_query(sql, _date_params(start_date, end_date))


# ==================================================================
# KPI 14 — Providers per state
# ==================================================================
@app.get("/api/charts/providers-per-state", tags=["charts"])
def chart_providers_per_state():
    sql = """
        SELECT
          state,
          COUNT(DISTINCT provider_id) AS providers
        FROM providers
        GROUP BY state
        ORDER BY providers DESC
    """
    return _run_query(sql, {})


# ==================================================================
# KPI 15, 16 — Claims & value by state
# ==================================================================
@app.get("/api/charts/state", tags=["charts"])
def chart_state(
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
):
    sql = """
        SELECT
          pa.state,
          COUNT(*)                         AS claim_count,
          COALESCE(SUM(c.claim_amount), 0) AS total_claimed,
          ROUND(COALESCE(AVG(c.claim_amount), 0), 2) AS avg_claim_amount
        FROM claims c
        JOIN patients pa ON c.patient_id = pa.patient_id
        WHERE (:start_date IS NULL OR c.claim_date >= :start_date)
          AND (:end_date   IS NULL OR c.claim_date <= :end_date)
        GROUP BY pa.state
        ORDER BY total_claimed DESC
    """
    return _run_query(sql, _date_params(start_date, end_date))


# ==================================================================
# KPI 17 — Top 5 states by payment ratio
# ==================================================================
@app.get("/api/charts/top-payout-states", tags=["charts"])
def chart_top_payout_states():
    sql = """
        SELECT
          pa.state,
          COALESCE(SUM(c.claim_amount), 0)   AS total_claimed,
          COALESCE(SUM(p.payment_amount), 0) AS total_paid,
          ROUND(
            COALESCE(SUM(p.payment_amount), 0)
            / NULLIF(SUM(c.claim_amount), 0) * 100, 2
          ) AS payment_ratio
        FROM claims c
        JOIN patients pa ON c.patient_id = pa.patient_id
        LEFT JOIN payments p ON c.claim_id = p.claim_id
        GROUP BY pa.state
        HAVING total_claimed > 0
        ORDER BY payment_ratio DESC
        LIMIT 5
    """
    return _run_query(sql, {})


# ==================================================================
# KPI 18, 19 — Patients headline
# ==================================================================
@app.get("/api/kpis/patients", tags=["kpis"])
def kpi_patients():
    sql = """
        SELECT
          (SELECT COUNT(DISTINCT patient_id) FROM patients) AS total_patients,
          (SELECT COUNT(*) FROM claims)
            / NULLIF((SELECT COUNT(DISTINCT patient_id) FROM patients), 0)
            AS claims_per_patient
    """
    rows = _run_query(sql, {})
    return rows[0] if rows else {}


# ==================================================================
# KPI 20 — Top patients
# ==================================================================
@app.get("/api/charts/top-patients", tags=["charts"])
def chart_top_patients(limit: int = Query(10, ge=1, le=50)):
    sql = f"""
        SELECT
          pa.patient_id,
          CONCAT(pa.first_name, ' ', pa.last_name) AS patient_name,
          pa.state,
          pa.age,
          COUNT(*)                                 AS claim_count,
          COALESCE(SUM(c.claim_amount), 0)         AS total_claimed
        FROM claims c
        JOIN patients pa ON c.patient_id = pa.patient_id
        GROUP BY pa.patient_id, patient_name, pa.state, pa.age
        ORDER BY total_claimed DESC
        LIMIT {int(limit)}
    """
    return _run_query(sql, {})


# ==================================================================
# KPI 21 — Age band distribution (filter-aware)
# ==================================================================
@app.get("/api/charts/age-bands", tags=["charts"])
def chart_age_bands(
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
):
    # Only count patients who filed at least one claim in the window.
    # COUNT(DISTINCT) prevents double-counting patients with multiple claims.
    sql = """
        SELECT
          CASE
            WHEN pa.age < 18 THEN '0-17'
            WHEN pa.age < 35 THEN '18-34'
            WHEN pa.age < 50 THEN '35-49'
            WHEN pa.age < 65 THEN '50-64'
            WHEN pa.age < 80 THEN '65-79'
            ELSE '80+'
          END      AS age_band,
          COUNT(DISTINCT pa.patient_id) AS patients
        FROM claims c
        JOIN patients pa ON c.patient_id = pa.patient_id
        WHERE (:start_date IS NULL OR c.claim_date >= :start_date)
          AND (:end_date   IS NULL OR c.claim_date <= :end_date)
        GROUP BY age_band
        ORDER BY age_band
    """
    return _run_query(sql, _date_params(start_date, end_date))


# ==================================================================
# KPI 23 — Payment lag stats
# ==================================================================
@app.get("/api/kpis/payment-lag", tags=["kpis"])
def kpi_payment_lag():
    sql = """
        SELECT
          ROUND(AVG(DATEDIFF(p.payment_date, c.claim_date)), 1) AS avg_lag_days,
          MIN(DATEDIFF(p.payment_date, c.claim_date))           AS min_lag,
          MAX(DATEDIFF(p.payment_date, c.claim_date))           AS max_lag,
          COUNT(*)                                              AS payments_counted
        FROM payments p
        JOIN claims c ON p.claim_id = c.claim_id
        WHERE p.payment_date IS NOT NULL
          AND c.claim_date IS NOT NULL
    """
    rows = _run_query(sql, {})
    return rows[0] if rows else {}


# ==================================================================
# KPI 23b — Payment lag histogram
# ==================================================================
@app.get("/api/charts/payment-lag-histogram", tags=["charts"])
def chart_payment_lag_histogram():
    sql = """
        SELECT
          CASE
            WHEN lag_days <= 7   THEN '0-7 days'
            WHEN lag_days <= 14  THEN '8-14 days'
            WHEN lag_days <= 30  THEN '15-30 days'
            WHEN lag_days <= 60  THEN '31-60 days'
            WHEN lag_days <= 90  THEN '61-90 days'
            ELSE '90+ days'
          END      AS lag_bucket,
          COUNT(*) AS payments
        FROM (
          SELECT DATEDIFF(p.payment_date, c.claim_date) AS lag_days
          FROM payments p
          JOIN claims c ON p.claim_id = c.claim_id
          WHERE p.payment_date IS NOT NULL
            AND c.claim_date IS NOT NULL
        ) t
        GROUP BY lag_bucket
        ORDER BY CASE lag_bucket
          WHEN '0-7 days'   THEN 1
          WHEN '8-14 days'  THEN 2
          WHEN '15-30 days' THEN 3
          WHEN '31-60 days' THEN 4
          WHEN '61-90 days' THEN 5
          ELSE 6
        END
    """
    return _run_query(sql, {})


# ==================================================================
# KPI 24 — Paid vs unpaid claims
# ==================================================================
@app.get("/api/charts/paid-vs-unpaid", tags=["charts"])
def chart_paid_vs_unpaid():
    sql = """
        SELECT
          SUM(CASE WHEN p.claim_id IS NOT NULL THEN 1 ELSE 0 END) AS paid_claims,
          SUM(CASE WHEN p.claim_id IS NULL     THEN 1 ELSE 0 END) AS unpaid_claims,
          ROUND(
            SUM(CASE WHEN p.claim_id IS NOT NULL THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0) * 100, 2
          ) AS paid_pct
        FROM claims c
        LEFT JOIN (SELECT DISTINCT claim_id FROM payments) p
               ON c.claim_id = p.claim_id
    """
    rows = _run_query(sql, {})
    return rows[0] if rows else {}


# ==================================================================
# Filters — populate dropdowns
# ==================================================================
@app.get("/api/filters/states", tags=["filters"])
def filter_states():
    sql = "SELECT DISTINCT state FROM patients WHERE state IS NOT NULL ORDER BY state"
    return _run_query(sql, {})


@app.get("/api/filters/statuses", tags=["filters"])
def filter_statuses():
    sql = "SELECT DISTINCT status FROM claims WHERE status IS NOT NULL ORDER BY status"
    return _run_query(sql, {})


@app.get("/api/filters/specialties", tags=["filters"])
def filter_specialties():
    sql = "SELECT DISTINCT specialty FROM providers WHERE specialty IS NOT NULL ORDER BY specialty"
    return _run_query(sql, {})


# ==================================================================
# Meta
# ==================================================================
@app.get("/api/meta/endpoints", tags=["meta"])
def meta_endpoints():
    return {
        "kpis": [
            "/api/kpis/claims", "/api/kpis/payments", "/api/kpis/rates",
            "/api/kpis/pending", "/api/kpis/patients", "/api/kpis/payment-lag",
        ],
        "charts": [
            "/api/charts/monthly-claims", "/api/charts/mom-growth",
            "/api/charts/status", "/api/charts/top-providers",
            "/api/charts/specialty", "/api/charts/providers-per-state",
            "/api/charts/state", "/api/charts/top-payout-states",
            "/api/charts/top-patients", "/api/charts/age-bands",
            "/api/charts/payment-lag-histogram", "/api/charts/paid-vs-unpaid",
        ],
        "filters": [
            "/api/filters/states", "/api/filters/statuses", "/api/filters/specialties",
        ],
        "admin": ["/api/cache/clear", "/api/cache/stats"],
        "health": ["/api/health"],
    }
