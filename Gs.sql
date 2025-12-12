/* ============================================================
   TAB 1 – Request 2a: WL and RL
   Grain: 1 row per (CM_DEAL_ID, CMPY_NM, LIST_TYPE)
   Employee: khurram.yousaf@db.com
   ============================================================ */

SELECT DISTINCT
       b.CR_DEAL_ID,
       b.CM_DEAL_ID,
       b.PRODUCTS,
       b.ROLE_NAME,
       b.INSIDER_ON_DT,
       b.INSIDER_OFF_DT,
       b.ON_DT,
       b.OFF_DT,
       b.LIST_TYPE,      -- WL or RL
       b.CMPY_NM,
       b.CLNT_FLG,
       b.COMPANY_ROLE,
       b.MIN_DATE_ANY_COMPANY_OF_DEAL_ADDED_ON_LIST,
       b.MAX_DATE_ANY_COMPANY_OF_DEAL_REMOVED_FROM_LIST,
       b.DL_CMPY_ID,
       b.CMPY_ID
FROM (
        SELECT DISTINCT
               d.CR_DEAL_ID,
               d.CM_DEAL_ID,
               dll.LIST_ADD_DT,      -- used later as LIST_ADD_DT
               di.CTRN_DT,           -- used later as CTRN_DT

               /* Product classification (same as original) */
               (SELECT cl.CLASSIFICATION_VALUE
                  FROM CLASSIFICATION cl
                 WHERE dp.PROD_NM_ID = cl.CLASSIFICATION_IDENTIFIER) AS PRODUCTS,

               /* Role name */
               rol.CLASSIFICATION_VALUE          AS ROLE_NAME,

               /* Insider / role dates (kept as in original – Req 1) */
               dt.INSIDER_ON_DT,
               dt.INSIDER_OFF_DT,
               dt.ON_DT,
               dt.OFF_DT,

               /* WL / RL list type text */
               lt.CLASSIFICATION_VALUE           AS LIST_TYPE,

               /* Company information */
               cp.CMPY_NM,
               dc.CLNT_FLG,
               cp.CMPY_RL                         AS COMPANY_ROLE,

               /* Deal-level min date any company added to a WL/RL (same logic) */
               (SELECT MIN(dll_inn.LIST_ADD_DT)
                  FROM CRU_AUDIT_OWNER.DL_LIST dll_inn
                  JOIN DEAL_COMPANY dc_inn
                    ON dc_inn.DL_CMPY_ID = dll_inn.DL_CMPY_ID
                 WHERE dc_inn.DL_ID      = d.DEAL_ID
                   AND dll_inn.LIST_TY_ID = dll.LIST_TY_ID
               ) AS MIN_DATE_ANY_COMPANY_OF_DEAL_ADDED_ON_LIST,

               /* Deal-level max removal date, or 'Still_on_LIST' (Req 3) */
               CASE
                    WHEN EXISTS (
                           SELECT 1
                             FROM DL_LIST dll_inn
                             JOIN DEAL_COMPANY dc_inn
                               ON dc_inn.DL_CMPY_ID = dll_inn.DL_CMPY_ID
                            WHERE dc_inn.DL_ID       = d.DEAL_ID
                              AND dll_inn.LIST_TY_ID = dll.LIST_TY_ID
                              AND dll_inn.LIST_REMOVAL_DT IS NULL
                              AND d.DL_WORKFLOW_STS NOT LIKE 'ARCHIVED'
                         )
                    THEN 'Still_on_LIST'
                    ELSE TO_CHAR(
                           MAX(dll_inn.LIST_REMOVAL_DT)
                         )
               END AS MAX_DATE_ANY_COMPANY_OF_DEAL_REMOVED_FROM_LIST,

               dc.DL_CMPY_ID,
               cp.CMPY_ID

        FROM   DEAL d
        INNER JOIN DEAL_COMPANY dc
                ON d.DEAL_ID = dc.DL_ID
        INNER JOIN CRU_OWNER.DEAL_TEAM dt
                ON dt.DEAL_ID = d.DEAL_ID
        INNER JOIN CLASSIFICATION rol
                ON rol.CLASSIFICATION_IDENTIFIER = dt.ROLE_ID
        INNER JOIN CRU_OWNER.EMPLOYEE e
                ON e.EMPLOYEE_ID = dt.EMPLOYEE_ID
        INNER JOIN CMPY cp
                ON cp.CMPY_ID = dc.CMPY_ID
        INNER JOIN DL_LIST dll
                ON dll.DL_CMPY_ID = dc.DL_CMPY_ID
        INNER JOIN CLASSIFICATION lt
                ON lt.CLASSIFICATION_IDENTIFIER = dll.LIST_TY_ID
        LEFT  JOIN DEAL_PRODUCT dp
                ON dp.DEAL_ID = d.DEAL_ID
        LEFT  JOIN DL_INS di
                ON di.DL_CMPY_ID = dc.DL_CMPY_ID
        LEFT  JOIN FNCL_INS fi
                ON fi.FNCL_INS_ID = di.FNCL_INS_ID

        WHERE 1 = 1

          /* ---------------------------------------------------
             Req 1 – Employee khurram.yousaf@db.com active on /
                     after 01-JAN-2022 (keep original logic)
             --------------------------------------------------- */
          AND e.EMPLOYEE_EMAIL = 'khurram.yousaf@db.com'
          AND (
                  (TRUNC(dt.INSIDER_OFF_DT) >= TO_DATE('01-JAN-2022','DD-MON-YYYY')
                   OR TRUNC(dt.INSIDER_OFF_DT) IS NULL)
               OR (TRUNC(dt.OFF_DT) >= TO_DATE('01-JAN-2022','DD-MON-YYYY')
                   OR TRUNC(dt.OFF_DT) IS NULL)
              )

          /* ---------------------------------------------------
             Restrict to WL / RL only (same as original)
             LIST_TYPE text comes from lt.CLASSIFICATION_VALUE
             --------------------------------------------------- */
          AND lt.CLASSIFICATION_VALUE IN ('WL','RL')

          /* ---------------------------------------------------
             Req 2 – At least one company on this deal was on
                     the WATCH LIST WITH INSTRUMENTS on or
                     after 01-JAN-2022.
             This is enforced at DEAL level via EXISTS.
             --------------------------------------------------- */
          AND EXISTS (
              SELECT 1
              FROM   DEAL_COMPANY dc_wl
              JOIN   DL_LIST dll_wl
                     ON dll_wl.DL_CMPY_ID = dc_wl.DL_CMPY_ID
              JOIN   DL_INS di_wl
                     ON di_wl.DL_CMPY_ID = dc_wl.DL_CMPY_ID
              JOIN   FNCL_INS fi_wl
                     ON fi_wl.FNCL_INS_ID = di_wl.FNCL_INS_ID
              WHERE  dc_wl.DL_ID        = d.DEAL_ID
                AND  dll_wl.LIST_TY_ID  = 325                -- WATCH LIST
                /* WL period intersects [01-JAN-2022, ∞) */
                AND  (TRUNC(dll_wl.LIST_REMOVAL_DT) >= TO_DATE('01-JAN-2022','DD-MON-YYYY')
                      OR TRUNC(dll_wl.LIST_REMOVAL_DT) IS NULL)
          )

          /* ---------------------------------------------------
             Req 4 – No companies on the deal were added to the
                     RESTRICTED LIST prior to 01-JAN-2022.
             If any RL add date < 2022 exists, exclude the deal.
             --------------------------------------------------- */
          AND NOT EXISTS (
              SELECT 1
              FROM   DEAL_COMPANY dc_rl
              JOIN   DL_LIST dll_rl
                     ON dll_rl.DL_CMPY_ID = dc_rl.DL_CMPY_ID
              WHERE  dc_rl.DL_ID       = d.DEAL_ID
                AND  dll_rl.LIST_TY_ID = 326                   -- RESTRICTED LIST
                AND  TRUNC(dll_rl.LIST_ADD_DT)
                         < TO_DATE('01-JAN-2022','DD-MON-YYYY')
          )

          /* ---------------------------------------------------
             Original removal-date filter (kept – part of date
             window logic for WL/RL entries).
             --------------------------------------------------- */
          AND (TRUNC(dll.LIST_REMOVAL_DT) >= TO_DATE('01-JAN-2022','DD-MON-YYYY')
               OR TRUNC(dll.LIST_REMOVAL_DT) IS NULL)

     ) b
/* -----------------------------------------------------------
   ORIGINAL outer filter – timing + “no company still on WL”
   (Req 3 already applied via MAX_DATE_* in subquery)
   ----------------------------------------------------------- */
WHERE (b.CTRN_DT IS NULL OR b.CTRN_DT > b.LIST_ADD_DT)
  AND b.MAX_DATE_ANY_COMPANY_OF_DEAL_REMOVED_FROM_LIST <> 'Still_on_LIST';
