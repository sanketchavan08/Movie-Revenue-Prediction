-- YTD window start
WITH base AS (
  SELECT emp_id,
         ib_designation,
         sts_updt_ts
  FROM   cru_owner.ibs_group_directory_upd_queue
  WHERE  sts_updt_ts >= DATE '2025-01-01'
),
ordered AS (
  SELECT emp_id,
         ib_designation,
         sts_updt_ts,
         LAG(ib_designation) OVER (PARTITION BY emp_id ORDER BY sts_updt_ts) AS prev_ib_designation
  FROM   base
),
changes AS (
  SELECT sts_updt_ts
  FROM   ordered
  WHERE  prev_ib_designation IS NOT NULL
  AND    ib_designation <> prev_ib_designation
)
SELECT
  COUNT(*)                                                    AS total_changes_ytd,
  (TRUNC(SYSDATE) - DATE '2025-01-01' + 1)                   AS days_elapsed_ytd,
  ROUND(COUNT(*) / (TRUNC(SYSDATE) - DATE '2025-01-01' + 1), 4) AS avg_changes_per_day_ytd,
  -- Optional: if you also want the average over only days that had changes:
  COUNT(DISTINCT TRUNC(sts_updt_ts))                          AS active_days,
  ROUND(COUNT(*) / COUNT(DISTINCT TRUNC(sts_updt_ts)), 4)     AS avg_changes_per_active_day
FROM changes;
