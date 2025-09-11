import pandas as pd
import os
import msoffcrypto
from datetime import datetime

def load_config(config_file):
    """Load configuration from the config file."""
    config = {}
    try:
        with open(config_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    except Exception as e:
        print(f"Error reading config file: {e}")
    return config

def decrypt_excel(input_file, password):
    """Decrypts the Excel file and returns the path to the decrypted file."""
    decrypted_file = os.path.join(os.path.dirname(input_file), 'decrypted_file.xlsx')
    try:
        with open(input_file, 'rb') as f:
            office_file = msoffcrypto.OfficeFile(f)
            office_file.load_key(password=password)
            with open(decrypted_file, 'wb') as df:
                office_file.decrypt(df)
        return decrypted_file
    except msoffcrypto.exceptions.DecryptionError:
        print("Error: Incorrect password or corrupted Excel file.")
        return None
    except Exception as e:
        print(f"Error decrypting Excel file: {e}")
        return None

def load_excel_to_dataframe(file_path):
    """Loads the decrypted Excel file into a pandas DataFrame."""
    try:
        df = pd.read_excel(file_path, header=None, engine='openpyxl')
        if df.empty:
            print("Error: Excel file is empty.")
            return None
        return df
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None
    finally:
        # Clean up the decrypted file
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Base directory for the project
    input_file = os.path.join(base_dir, 'input', 'your_file.xlsx')  # Input file path
    output_dir = os.path.join(base_dir, 'output')  # Output directory
    config_file = os.path.join(base_dir, 'scripts', 'config.txt')  # Config file path

    # Generate dynamic output file name
    current_date = datetime.now().strftime('%Y%m%d')
    output_file = os.path.join(output_dir, f'emp_{current_date}.txt')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Prevent directory name collision with the output file
    if os.path.isdir(output_file):
        print(f"Error: A directory named '{output_file}' already exists. Please remove or rename it.")
        return

    # Load config
    config = load_config(config_file)
    password = config.get('password')
    if not password:
        print("Error: Password not found in config file.")
        return

    # Decrypt the Excel file
    decrypted_file = decrypt_excel(input_file, password)
    if not decrypted_file:
        return

    # Load the decrypted Excel file into a DataFrame
    df = load_excel_to_dataframe(decrypted_file)
    if df is None:
        return

    # Extract first and last rows
    first_row = df.iloc[0]
    last_row = df.iloc[-1] if len(df) > 1 else first_row

    # Process the middle rows
    middle_rows = df.iloc[1:-1] if len(df) > 2 else pd.DataFrame()
    columns_to_format = [2, 5, 10]  # Columns C, F, and K (zero-indexed)

    
    # Convert numeric columns and format rows
def format_row(row):
    for col in range(len(row)):
        if col in [2, 4, 10]:  # Columns C, E, K (zero-indexed)
            if isinstance(row[col], (float, int)):
                # Format with 6 digits after decimal and replace '.' with ','
                row[col] = f"{row[col]:.6f}".replace('.', ',')
        elif col == 5:  # Column F (YYYYMMDD)
            if isinstance(row[col], pd.Timestamp):
                row[col] = row[col].strftime('%Y%m%d')  # Convert Timestamp to YYYYMMDD
            elif isinstance(row[col], (float, int)):
                row[col] = str(int(row[col]))  # Keep as integer in string form
        elif col == 6:  # Column G (integer)
            if isinstance(row[col], float) and row[col].is_integer():
                row[col] = int(row[col])  # Convert float-like integers to int
            elif pd.isna(row[col]):
                row[col] = ''  # Handle NaN
        elif pd.isna(row[col]):  # Handle empty columns (e.g., H)
            row[col] = ''
    return ';'.join(map(str, row))

    processed_rows = middle_rows.apply(format_row, axis=1) if not middle_rows.empty else []

    # Write to output file
    try:
        with open(output_file, 'w') as f:
            f.write(';'.join(map(str, first_row)) + '\n')  # Write first row
            if not middle_rows.empty:
                f.writelines(processed_rows.apply(lambda x: x + '\n'))  # Write processed rows
            f.write(';'.join(map(str, last_row)) + '\n')  # Write last row
        print(f"File processed successfully. Output saved to: {output_file}")
    except PermissionError:
        print(f"Error: Permission denied when trying to write to '{output_file}'. Ensure it is not a directory or locked.")
    except Exception as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    main()




-- === Point-in-time WL check, with concatenated (CR_DEAL_ID|RGN_CD) tuples ===
WITH
-- 1) Paste your Excel rows here (generate UNION ALL lines in Excel)
pairs AS (
  SELECT
    15696017    AS trade_request_id,
    'megan_kwong@db.com' AS email,
    DATE '2025-07-28' AS trade_dt,                -- column C (TRUNC(CREATEDDT))
    'AUTO_APPROVE' AS request_final_status,       -- column D
    8588080     AS hr_id,                         -- column E
    'HONG KONG' AS country,                       -- column F
    'APAC'      AS region_from_sheet,             -- column G (keep if you want side-by-side)
    'US02079K3059' AS isin                        -- column H
  FROM dual
  UNION ALL
  SELECT
    15699095, 'manjusha.gole@db.com',
    DATE '2025-07-28',
    'AUTO_APPROVE',
    8631432,
    'INDIA',
    'APAC',
    'INE200M01039'
  FROM dual
  -- ... add the rest of your rows
),

-- 2) Watchlist history. Carry CR_DEAL_ID and RGN_CD from your base query.
base AS (
  SELECT
    fi.fncl_ins_isin,
    dll.list_add_dt,
    dll.list_removal_dt,
    di.crtn_dt,
    di.off_dt,
    di.cr_deal_id,         -- <== from your screenshot (use exact column name)
    de.rgn_cd              -- <== region code from DEAL
  FROM cru_owner.dl_list        dll
  JOIN cru_owner.deal_company   dc ON dc.dl_cmpy_id  = dll.dl_cmpy_id
  JOIN cru_owner.cmpy           cp ON cp.cmpy_id     = dc.cmpy_id
  JOIN cru_owner.deal           de ON de.deal_id     = dc.deal_id     -- adjust if your join differs
  JOIN cru_owner.dl_ins         di ON di.dl_cmpy_id  = dc.dl_cmpy_id
  JOIN cru_owner.fncl_ins       fi ON fi.fncl_ins_id = di.fncl_ins_id
  WHERE dll.list_ty_id = 325    -- Watchlist
),

-- 3) Point-in-time join to keep only rows active on the trade date
joined AS (
  SELECT
    p.*,
    b.cr_deal_id,
    b.rgn_cd
  FROM pairs p
  LEFT JOIN base b
    ON b.fncl_ins_isin = p.isin
   AND b.crtn_dt                        <= p.trade_dt
   AND NVL(b.off_dt, DATE '9999-12-31') >  p.trade_dt
   AND b.list_add_dt                    <= p.trade_dt
   AND (b.list_removal_dt IS NULL OR b.list_removal_dt >= p.trade_dt)
)

-- 4) Final: one row per Excel line with YES/NO and concatenated tuples
SELECT
  j.trade_request_id,
  j.email,
  j.trade_dt,
  j.request_final_status,
  j.hr_id,
  j.country,
  j.region_from_sheet,
  j.isin,
  CASE WHEN COUNT(j.cr_deal_id) > 0 THEN 'YES' ELSE 'NO' END AS wl_yn,
  CASE
    WHEN COUNT(j.cr_deal_id) = 0 THEN NULL
    ELSE
      LISTAGG(pair_txt, ', ') WITHIN GROUP (ORDER BY pair_txt)
  END AS deal_region_tuples   -- e.g. '(E00555808|EMEA), (E00558734|EMEA)'
FROM (
  -- de-dup pair text before aggregating (safer than LISTAGG DISTINCT on older versions)
  SELECT DISTINCT
         trade_request_id, email, trade_dt, request_final_status, hr_id,
         country, region_from_sheet, isin,
         cr_deal_id, rgn_cd,
         '(' || cr_deal_id || '|' || NVL(rgn_cd,'NA') || ')' AS pair_txt
  FROM joined
) j
GROUP BY
  j.trade_request_id, j.email, j.trade_dt, j.request_final_status,
  j.hr_id, j.country, j.region_from_sheet, j.isin
ORDER BY j.trade_request_id, j.trade_dt, j.isin;
