-- =====================================================================
-- analytics_queries.sql
-- Insurance Analytics Dashboard — query pack (runnable version)
-- All 25 KPIs across 7 themes.
--
-- Usage:
--   mysql -u root -p insurance_analytics < analytics_queries.sql
--
-- To filter by date, replace the whole `WHERE` clause's NULL comparisons
-- with real values (see note at the bottom of this file).
-- =====================================================================

USE insurance_analytics;

-- =====================================================================
-- Sanity check — confirm the four tables loaded correctly
-- =====================================================================
SELECT 'patients'  AS tbl, COUNT(*) AS n FROM patients
UNION ALL SELECT 'providers', COUNT(*) FROM providers
UNION ALL SELECT 'claims',    COUNT(*) FROM claims
UNION ALL SELECT 'payments',  COUNT(*) FROM payments;


-- =====================================================================
-- KPI 1, 2, 6 — Claims headline metrics
-- =====================================================================
SELECT
  COUNT(DISTINCT claim_id)        AS total_claims,
  COALESCE(SUM(claim_amount), 0)  AS total_claimed,
  COALESCE(AVG(claim_amount), 0)  AS avg_claim_amount
FROM claims;


-- =====================================================================
-- KPI 3, 4, 22 — Payments headline metrics
-- Payment Ratio = total paid ÷ total claimed
-- =====================================================================
SELECT
  (SELECT COALESCE(SUM(payment_amount), 0) FROM payments) AS total_paid,
  (SELECT COALESCE(AVG(payment_amount), 0) FROM payments) AS avg_payment_amount,
  ROUND(
    (SELECT COALESCE(SUM(payment_amount), 0) FROM payments)
    / NULLIF((SELECT COALESCE(SUM(claim_amount), 0) FROM claims), 0) * 100,
    2
  ) AS payment_ratio;


-- =====================================================================
-- KPI 5 — Monthly claim volume
-- =====================================================================
SELECT
  DATE_FORMAT(claim_date, '%Y-%m') AS month,
  COUNT(*)                         AS claims,
  COALESCE(SUM(claim_amount), 0)   AS claimed_value
FROM claims
GROUP BY month
ORDER BY month;


-- =====================================================================
-- KPI 7 — Month-over-month claim growth
-- =====================================================================
SELECT
  month,
  claims,
  LAG(claims) OVER (ORDER BY month) AS prev_month_claims,
  ROUND(
    (claims - LAG(claims) OVER (ORDER BY month))
    / NULLIF(LAG(claims) OVER (ORDER BY month), 0) * 100,
    2
  ) AS mom_growth_pct
FROM (
  SELECT DATE_FORMAT(claim_date, '%Y-%m') AS month, COUNT(*) AS claims
  FROM claims
  GROUP BY month
) t
ORDER BY month;


-- =====================================================================
-- KPI 8 — Claims by status
-- =====================================================================
SELECT
  status,
  COUNT(*)                       AS n,
  COALESCE(SUM(claim_amount), 0) AS value
FROM claims
GROUP BY status
ORDER BY n DESC;


-- =====================================================================
-- KPI 9, 25 — Approval & rejection rate
-- =====================================================================
SELECT
  ROUND(SUM(status = 'Approved') / NULLIF(COUNT(*), 0) * 100, 2) AS approval_rate,
  ROUND(SUM(status = 'Rejected') / NULLIF(COUNT(*), 0) * 100, 2) AS rejection_rate,
  ROUND(SUM(status = 'Pending')  / NULLIF(COUNT(*), 0) * 100, 2) AS pending_rate
FROM claims;


-- =====================================================================
-- KPI 10 — Pending claims value
-- =====================================================================
SELECT
  COUNT(*)                       AS pending_count,
  COALESCE(SUM(claim_amount), 0) AS pending_value
FROM claims
WHERE status = 'Pending';


-- =====================================================================
-- KPI 11 — Top 10 providers by claim value
-- =====================================================================
SELECT
  p.provider_id,
  p.name                       AS provider_name,
  p.specialty,
  p.state,
  COUNT(*)                     AS claim_count,
  COALESCE(SUM(c.claim_amount), 0) AS total_claimed
FROM claims c
JOIN providers p ON c.provider_id = p.provider_id
GROUP BY p.provider_id, p.name, p.specialty, p.state
ORDER BY total_claimed DESC
LIMIT 10;


-- =====================================================================
-- KPI 12 — Claims by specialty
-- =====================================================================
SELECT
  p.specialty,
  COUNT(*)                         AS claim_count,
  COALESCE(SUM(c.claim_amount), 0) AS total_claimed,
  ROUND(COALESCE(AVG(c.claim_amount), 0), 2) AS avg_claim_amount
FROM claims c
JOIN providers p ON c.provider_id = p.provider_id
GROUP BY p.specialty
ORDER BY claim_count DESC;


-- =====================================================================
-- KPI 13 — Avg claim per provider (outliers, min 5 claims)
-- =====================================================================
SELECT
  p.provider_id,
  p.name AS provider_name,
  p.specialty,
  COUNT(*)             AS claim_count,
  ROUND(AVG(c.claim_amount), 2)  AS avg_claim_amount,
  COALESCE(SUM(c.claim_amount), 0) AS total_claimed
FROM claims c
JOIN providers p ON c.provider_id = p.provider_id
GROUP BY p.provider_id, p.name, p.specialty
HAVING claim_count >= 5
ORDER BY avg_claim_amount DESC
LIMIT 20;


-- =====================================================================
-- KPI 14 — Providers per state
-- =====================================================================
SELECT
  state,
  COUNT(DISTINCT provider_id) AS providers
FROM providers
GROUP BY state
ORDER BY providers DESC;


-- =====================================================================
-- KPI 15, 16 — Claims & value by state
-- =====================================================================
SELECT
  pa.state,
  COUNT(*)                         AS claim_count,
  COALESCE(SUM(c.claim_amount), 0) AS total_claimed,
  ROUND(COALESCE(AVG(c.claim_amount), 0), 2) AS avg_claim_amount
FROM claims c
JOIN patients pa ON c.patient_id = pa.patient_id
GROUP BY pa.state
ORDER BY total_claimed DESC;


-- =====================================================================
-- KPI 17 — Top 5 states by payment ratio
-- =====================================================================
SELECT
  pa.state,
  COALESCE(SUM(c.claim_amount), 0)     AS total_claimed,
  COALESCE(SUM(p.payment_amount), 0)   AS total_paid,
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
LIMIT 5;


-- =====================================================================
-- KPI 18, 19 — Patients headline
-- =====================================================================
SELECT
  (SELECT COUNT(DISTINCT patient_id) FROM patients) AS total_patients,
  (SELECT COUNT(*) FROM claims)
    / NULLIF((SELECT COUNT(DISTINCT patient_id) FROM patients), 0)
                                                     AS claims_per_patient;


-- =====================================================================
-- KPI 20 — Top 10 patients by claim value
-- =====================================================================
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
LIMIT 10;


-- =====================================================================
-- KPI 21 — Age band distribution
-- =====================================================================
SELECT
  CASE
    WHEN age < 18 THEN '0-17'
    WHEN age < 35 THEN '18-34'
    WHEN age < 50 THEN '35-49'
    WHEN age < 65 THEN '50-64'
    WHEN age < 80 THEN '65-79'
    ELSE '80+'
  END     AS age_band,
  COUNT(*) AS patients
FROM patients
GROUP BY age_band
ORDER BY age_band;


-- =====================================================================
-- KPI 23 — Claim-to-payment lag (days)
-- =====================================================================
SELECT
  ROUND(AVG(DATEDIFF(p.payment_date, c.claim_date)), 1) AS avg_lag_days,
  MIN(DATEDIFF(p.payment_date, c.claim_date))           AS min_lag,
  MAX(DATEDIFF(p.payment_date, c.claim_date))           AS max_lag,
  COUNT(*)                                              AS payments_counted
FROM payments p
JOIN claims c ON p.claim_id = c.claim_id
WHERE p.payment_date IS NOT NULL
  AND c.claim_date IS NOT NULL;


-- =====================================================================
-- KPI 23b — Payment lag histogram (bucketed)
-- =====================================================================
SELECT
  CASE
    WHEN lag_days <= 7   THEN '0-7 days'
    WHEN lag_days <= 14  THEN '8-14 days'
    WHEN lag_days <= 30  THEN '15-30 days'
    WHEN lag_days <= 60  THEN '31-60 days'
    WHEN lag_days <= 90  THEN '61-90 days'
    ELSE '90+ days'
  END          AS lag_bucket,
  COUNT(*)     AS payments
FROM (
  SELECT DATEDIFF(p.payment_date, c.claim_date) AS lag_days
  FROM payments p
  JOIN claims c ON p.claim_id = c.claim_id
  WHERE p.payment_date IS NOT NULL
    AND c.claim_date IS NOT NULL
) t
GROUP BY lag_bucket
ORDER BY
  CASE lag_bucket
    WHEN '0-7 days'   THEN 1
    WHEN '8-14 days'  THEN 2
    WHEN '15-30 days' THEN 3
    WHEN '31-60 days' THEN 4
    WHEN '61-90 days' THEN 5
    ELSE 6
  END;



-- =====================================================================
-- KPI 24 — Paid vs unpaid claims
-- =====================================================================
SELECT
  SUM(CASE WHEN p.claim_id IS NOT NULL THEN 1 ELSE 0 END) AS paid_claims,
  SUM(CASE WHEN p.claim_id IS NULL     THEN 1 ELSE 0 END) AS unpaid_claims,
  ROUND(
    SUM(CASE WHEN p.claim_id IS NOT NULL THEN 1 ELSE 0 END)
    / NULLIF(COUNT(*), 0) * 100, 2
  ) AS paid_pct
FROM claims c
LEFT JOIN (SELECT DISTINCT claim_id FROM payments) p
       ON c.claim_id = p.claim_id;


-- =====================================================================
-- KPI 4b — Overall payment ratio breakdown by status
-- =====================================================================
SELECT
  c.status,
  COUNT(DISTINCT c.claim_id)           AS claims,
  COALESCE(SUM(c.claim_amount), 0)     AS claimed,
  COALESCE(SUM(p.payment_amount), 0)   AS paid,
  ROUND(
    COALESCE(SUM(p.payment_amount), 0)
    / NULLIF(SUM(c.claim_amount), 0) * 100, 2
  ) AS ratio
FROM claims c
LEFT JOIN payments p ON c.claim_id = p.claim_id
GROUP BY c.status
ORDER BY claims DESC;


-- =====================================================================
-- Convenience view — claims fully joined
-- Used by the API for ad-hoc analysis.
-- =====================================================================
CREATE OR REPLACE VIEW v_claims_full AS
SELECT
  c.claim_id,
  c.claim_date,
  c.claim_amount,
  c.status,
  c.patient_id,
  c.provider_id,
  pa.state          AS patient_state,
  pa.city           AS patient_city,
  pa.age            AS patient_age,
  pa.gender         AS patient_gender,
  pr.specialty      AS provider_specialty,
  pr.state          AS provider_state,
  pr.name           AS provider_name,
  p.payment_id,
  p.payment_date,
  p.payment_amount,
  DATEDIFF(p.payment_date, c.claim_date) AS payment_lag_days
FROM claims c
LEFT JOIN patients  pa ON c.patient_id  = pa.patient_id
LEFT JOIN providers pr ON c.provider_id = pr.provider_id
LEFT JOIN payments  p  ON c.claim_id    = p.claim_id;


-- =====================================================================
-- Quick verification: sanity-check the view
-- =====================================================================
SELECT
  COUNT(*)                                     AS total_rows,
  SUM(CASE WHEN payment_amount IS NOT NULL THEN 1 ELSE 0 END) AS with_payments
FROM v_claims_full;


-- =====================================================================
-- HOW TO APPLY A DATE FILTER
-- ---------------------------------------------------------------------
-- The API layer passes :start_date and :end_date as bound parameters.
-- To test manually in MySQL, replace the WHERE clause, e.g.:
--
--   WHERE claim_date BETWEEN '2024-01-01' AND '2024-12-31'
--
-- Or comment out the WHERE entirely for all-time data.
--
-- The general pattern used by the API is:
--
--   WHERE (:start_date IS NULL OR claim_date >= :start_date)
--     AND (:end_date   IS NULL OR claim_date <= :end_date)
--
-- which works because MySQL evaluates the `IS NULL` short-circuit
-- for each row and skips the comparison when no filter is provided.
-- =====================================================================