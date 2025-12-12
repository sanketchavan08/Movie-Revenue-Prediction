        ON cp.CMPY_ID = dc.CMPY_ID
INNER JOIN DL_LIST dll
        ON dll.DL_CMPY_ID = dc.DL_CMPY_ID
INNER JOIN CLASSIFICATION lt
        ON lt.CLASSIFICATION_IDENTIFIER = dll.LIST_TY_ID
INNER JOIN DL_INS di
        ON di.DL_CMPY_ID = dc.DL_CMPY_ID
INNER JOIN FNCL_INS fi
        ON fi.FNCL_INS_ID = di.FNCL_INS_ID
WHERE  1 = 1

  /* -----------------------------------------------------------
     Deal universe: only deals that appeared in Tab 1 (Q1).
     You can materialise Q1 into a temp table or CTE and
     reference it here – placeholder shown as TAB1_RESULTS.
     ----------------------------------------------------------- */
  AND de.CM_DEAL_ID IN (
          SELECT DISTINCT CM_DEAL_ID
          FROM   TAB1_RESULTS      -- <-- replace with Q1 result set / temp table
      )

  /* -----------------------------------------------------------
     Req 1 alignment – same employee & insider time window
     as Tab 1 so business sees a consistent universe.
     (Kept exactly as in Q1.)
     ----------------------------------------------------------- */
  AND e.EMPLOYEE_EMAIL = 'khurram.yousaf@db.com'
  AND (
          (TRUNC(dt.INSIDER_OFF_DT) >= TO_DATE('01-JAN-2022','DD-MON-YYYY')
           OR TRUNC(dt.INSIDER_OFF_DT) IS NULL)
       OR (TRUNC(dt.OFF_DT) >= TO_DATE('01-JAN-2022','DD-MON-YYYY')
           OR TRUNC(dt.OFF_DT) IS NULL)
      )

  /* -----------------------------------------------------------
     WL ONLY – Tab 2 is "Watch List additions only".
     LIST_TY_ID 325 = WL (same coding as before).
     ----------------------------------------------------------- */
  AND dll.LIST_TY_ID = 325           -- Watch List only

  /* -----------------------------------------------------------
     Req 2 alignment – WL WITH INSTRUMENTS and in the same
     2022+ window as Tab 1. Because this query is already at
     ISIN level, "with instruments" is enforced via join to
     FNCL_INS and ISIN non-null.
     ----------------------------------------------------------- */
  AND fi.FNCL_INS_ISIN IS NOT NULL

  /* WL period must intersect [01-JAN-2022, ∞) – same window
     logic we used in Q1 for list_removal_dt. */
  AND (
          TRUNC(dll.LIST_REMOVAL_DT) >= TO_DATE('01-JAN-2022','DD-MON-YYYY')
       OR TRUNC(dll.LIST_REMOVAL_DT) IS NULL
      )

  /* -----------------------------------------------------------
     Req 4 alignment – no RL before 01-JAN-2022.
     Repeat the NOT EXISTS from Q1 so Tab 2 never shows
     instruments for deals disqualified by early RL history.
     ----------------------------------------------------------- */
  AND NOT EXISTS (
        SELECT 1
        FROM   DEAL_COMPANY dc_rl
        JOIN   DL_LIST dll_rl
               ON dll_rl.DL_CMPY_ID = dc_rl.DL_CMPY_ID
        WHERE  dc_rl.DL_ID       = de.DEAL_ID
          AND  dll_rl.LIST_TY_ID = 326    -- Restricted List
          AND  TRUNC(dll_rl.LIST_ADD_DT)
                   < TO_DATE('01-JAN-2022','DD-MON-YYYY')
      )

/* Optional: If you want to mimic the Q1 outer timing rule
   (ctrn_dt > list_add_dt) at ISIN level, you can add:

   AND (di.CTRN_DT IS NULL OR di.CTRN_DT > dll.LIST_ADD_DT)

   Only do this if business confirms they want the same
   timing definition applied at instrument level. */
ORDER BY
       de.CM_DEAL_ID,
       cp.CMPY_NM,
       fi.FNCL_INS_ISIN,
       DATE_ADDED_TO_WL;
