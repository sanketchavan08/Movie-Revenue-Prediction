import pandas as pd
import os

# File paths
input_path = os.path.join("input", "Final_List.xlsx")
output_path = os.path.join("output", "Final_List_Updated.xlsx")

# Read Excel sheets
pre_clearance_df = pd.read_excel(input_path, sheet_name="pre-clearance_trade")
missed_trades_df = pd.read_excel(input_path, sheet_name="missed_trades_last2yrs")

# Strip column names
pre_clearance_df.columns = pre_clearance_df.columns.str.strip()
missed_trades_df.columns = missed_trades_df.columns.str.strip()

# Convert timestamps to date only
pre_clearance_df["REQUEST_TS"] = pd.to_datetime(pre_clearance_df["REQUEST_TS"]).dt.date
missed_trades_df["Withdrawal Timestamp"] = pd.to_datetime(missed_trades_df["Withdrawal Timestamp"]).dt.date

# Normalize Employee IDs
pre_clearance_df["HR_EMPLOYEE_ID"] = pre_clearance_df["HR_EMPLOYEE_ID"].astype(str).str.strip().str.lstrip("'")
missed_trades_df["Employee Number"] = missed_trades_df["Employee Number"].astype(str).str.strip().str.lstrip("'")

# Matching loop
for i, missed_row in missed_trades_df.iterrows():
    emp_id = missed_row["Employee Number"]
    withdrawal_date = missed_row["Withdrawal Timestamp"]
    normalized_shares = abs(int(missed_row["Number of Shares"]))

    # === Full Match ===
    full_match = pre_clearance_df[
        (pre_clearance_df["HR_EMPLOYEE_ID"] == emp_id) &
        (pre_clearance_df["QUANTITY"].astype(int) == normalized_shares) &
        (pre_clearance_df["REQUEST_TS"] <= withdrawal_date)
    ]

    if not full_match.empty:
        match = full_match.sort_values(by="REQUEST_TS", ascending=False).iloc[0]
        missed_trades_df.at[i, "Match found in etra?"] = "Yes"
        missed_trades_df.at[i, "Match Type"] = "Full Match"
        missed_trades_df.at[i, "ETRA_TRADE_ID"] = match["TRADE_REQUEST_ID"]
        missed_trades_df.at[i, "ETRA_QUANTITY"] = match["QUANTITY"]
        missed_trades_df.at[i, "ETRA_REQUEST_TS"] = match["REQUEST_TS"]
        missed_trades_df.at[i, "STATUS"] = match["STATUS_CODE"]
        missed_trades_df.at[i, "ETRA_VALUE"] = match["VALUE"]
        continue  # Skip to next row

    # === Partial Match: Only if full match didn't happen ===
    if missed_trades_df.at[i, "Match found in etra?"] in ["", "No", None]:
        partial_match = pre_clearance_df[
            (pre_clearance_df["HR_EMPLOYEE_ID"] == emp_id) &
            (pre_clearance_df["REQUEST_TS"] == withdrawal_date)
        ]

        if not partial_match.empty:
            match = partial_match.iloc[0]
            missed_trades_df.at[i, "Match found in etra?"] = "Yes"
            missed_trades_df.at[i, "Match Type"] = "Partial Match"
            missed_trades_df.at[i, "ETRA_TRADE_ID"] = match["TRADE_REQUEST_ID"]
            missed_trades_df.at[i, "ETRA_QUANTITY"] = match["QUANTITY"]
            missed_trades_df.at[i, "ETRA_REQUEST_TS"] = match["REQUEST_TS"]
            missed_trades_df.at[i, "STATUS"] = match["STATUS_CODE"]
            missed_trades_df.at[i, "ETRA_VALUE"] = match["VALUE"]

# Write results to new output file
with pd.ExcelWriter(output_path, engine="openpyxl", mode="w") as writer:
    pre_clearance_df.to_excel(writer, sheet_name="pre-clearance_trade", index=False)
    missed_trades_df.to_excel(writer, sheet_name="missed_trades_last2yrs", index=False)

print(f"✅ Matching complete. Output saved to: {output_path}")
