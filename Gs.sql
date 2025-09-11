WITH
pairs AS (   -- your existing Excel rows go here (unchanged)
  SELECT 15696017 AS trade_request_id, 'megan_kwong@db.com' AS email,
         DATE '2025-07-28' AS trade_dt, 'AUTO_APPROVE' AS request_final_status,
         8588080 AS hr_id, 'HONG KONG' AS country, 'APAC' AS region_from_sheet,
         'US02079K3059' AS isin FROM dual
  UNION ALL
  SELECT 15699095, 'manjusha.gole@db.com', DATE '2025-07-28', 'AUTO_APPROVE',
         8631432, 'INDIA', 'APAC', 'INE200M01039' FROM dual
  UNION ALL
  SELECT 15837722, 'hamid.khaliquec@db.com', DATE '2025-09-10', 'AUTO_APPROVE',
         8470077, 'UNITED STATES', 'AMERICAS', 'US9311421039' FROM dual
),

wl_base AS (   -- same as before
  SELECT
    fi.fncl_ins_isin,
    dll.list_add_dt,
    dll.list_removal_dt,
    di.crtn_dt,
    di.off_dt,
    di.cr_deal_id,
    de.rgn_cd
  FROM cru_owner.dl_list        dll
  JOIN cru_owner.deal_company   dc ON dc.dl_cmpy_id  = dll.dl_cmpy_id
  JOIN cru_owner.deal           de ON de.deal_id     = dc.deal_id
  JOIN cru_owner.dl_ins         di ON di.dl_cmpy_id  = dc.dl_cmpy_id
  JOIN cru_owner.fncl_ins       fi ON fi.fncl_ins_id = di.fncl_ins_id
  WHERE dll.list_ty_id = 325
),

wl_joined AS (   -- same as before
  SELECT
    p.trade_request_id, p.email, p.trade_dt, p.request_final_status,
    p.hr_id, p.country, p.region_from_sheet, p.isin,
    w.cr_deal_id, w.rgn_cd
  FROM pairs p
  LEFT JOIN wl_base w
    ON w.fncl_ins_isin = p.isin
   AND w.crtn_dt                        <= p.trade_dt
   AND NVL(w.off_dt, DATE '9999-12-31') >  p.trade_dt
   AND w.list_add_dt                    <= p.trade_dt
   AND (w.list_removal_dt IS NULL OR w.list_removal_dt >= p.trade_dt)
),

wl_agg AS (   -- same as before
  SELECT
    trade_request_id, email, trade_dt, request_final_status,
    hr_id, country, region_from_sheet, isin,
    CASE WHEN COUNT(cr_deal_id) > 0 THEN 'YES' ELSE 'NO' END AS wl_yn,
    CASE WHEN COUNT(cr_deal_id) = 0 THEN NULL
         ELSE LISTAGG(pair_txt, ', ') WITHIN GROUP (ORDER BY pair_txt) END
      AS deal_region_tuples
  FROM (
    SELECT DISTINCT
           trade_request_id, email, trade_dt, request_final_status,
           hr_id, country, region_from_sheet, isin,
           cr_deal_id, rgn_cd,
           '(' || cr_deal_id || '|' || NVL(rgn_cd,'NA') || ')' AS pair_txt
    FROM wl_joined
  )
  GROUP BY trade_request_id, email, trade_dt, request_final_status,
           hr_id, country, region_from_sheet, isin
),

-- (1) NEW
emp_base AS (
  SELECT
    deal_id      AS cr_deal_id,
    db_people_id,
    start_date,
    end_date
  FROM cru_owner.v_wallis_deal_team e
  WHERE e.db_people_id IN (SELECT DISTINCT hr_id FROM pairs)
    AND e.start_date <= DATE '2025-09-11'
    AND (e.end_date IS NULL OR e.end_date >= DATE '2025-07-27')
),

-- (2) NEW
emp_joined AS (
  SELECT
    p.trade_request_id, p.email, p.trade_dt, p.request_final_status,
    p.hr_id, p.country, p.region_from_sheet, p.isin,
    e.cr_deal_id
  FROM pairs p
  LEFT JOIN emp_base e
    ON e.db_people_id = p.hr_id
   AND e.start_date <= p.trade_dt
   AND (e.end_date IS NULL OR e.end_date >= p.trade_dt)
),

-- (3) NEW
emp_agg AS (
  SELECT
    trade_request_id, email, trade_dt, request_final_status,
    hr_id, country, region_from_sheet, isin,
    CASE WHEN COUNT(cr_deal_id) > 0 THEN 'YES' ELSE 'NO' END AS emp_on_deal_yn,
    CASE WHEN COUNT(cr_deal_id) = 0 THEN NULL
         ELSE LISTAGG(cr_deal_id, ',') WITHIN GROUP (ORDER BY cr_deal_id) END
      AS emp_deals
  FROM (
    SELECT DISTINCT
           trade_request_id, email, trade_dt, request_final_status,
           hr_id, country, region_from_sheet, isin, cr_deal_id
    FROM emp_joined
  )
  GROUP BY trade_request_id, email, trade_dt, request_final_status,
           hr_id, country, region_from_sheet, isin
)

-- (4) CHANGED final SELECT
SELECT
  p.trade_request_id,
  p.email,
  p.trade_dt,
  p.request_final_status,
  p.hr_id,
  p.country,
  p.region_from_sheet,
  p.isin,
  w.wl_yn,
  w.deal_region_tuples,
  e.emp_on_deal_yn,
  e.emp_deals
FROM pairs p
LEFT JOIN wl_agg  w USING (trade_request_id, email, trade_dt, request_final_status,
                           hr_id, country, region_from_sheet, isin)
LEFT JOIN emp_agg e USING (trade_request_id, email, trade_dt, request_final_status,
                           hr_id, country, region_from_sheet, isin)
ORDER BY p.trade_request_id, p.trade_dt, p.isin;
