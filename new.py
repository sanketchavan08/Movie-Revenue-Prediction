import pandas as pd
import os

# Define input/output paths
input_path = os.path.join("input", "Final_List.xlsx")
output_path = os.path.join("output", "Final_List_Updated.xlsx")

# Read sheets from input file
pre_clearance_df = pd.read_excel(input_path, sheet_name="pre-clearance_trade")
missed_trades_df = pd.read_excel(input_path, sheet_name="missed_trades_last2yrs")

# Clean column names
pre_clearance_df.columns = pre_clearance_df.columns.str.strip()
missed_trades_df.columns = missed_trades_df.columns.str.strip()

# Convert timestamps to dates
pre_clearance_df["REQUEST_TS"] = pd.to_datetime(pre_clearance_df["REQUEST_TS"]).dt.date
missed_trades_df["Withdrawal Timestamp"] = pd.to_datetime(missed_trades_df["Withdrawal Timestamp"]).dt.date

# Matching logic
for i, missed_row in missed_trades_df.iterrows():
    matched_row = pre_clearance_df[
        (pre_clearance_df["HR_EMPLOYEE_ID"] == missed_row["Employee Number"]) &
        (pre_clearance_df["QUANTITY"] == missed_row["Number of Shares"]) &
        (pre_clearance_df["REQUEST_TS"] <= missed_row["Withdrawal Timestamp"])
    ]
    
    if not matched_row.empty:
        match = matched_row.sort_values(by="REQUEST_TS", ascending=False).iloc[0]
        missed_trades_df.at[i, "Match found in etra?"] = "Yes"
        missed_trades_df.at[i, "ETRA_TRADE_ID"] = match["TRADE_REQUEST_ID"]
        missed_trades_df.at[i, "ETRA_QUANTITY"] = match["QUANTITY"]
        missed_trades_df.at[i, "ETRA_REQUEST_TS"] = match["REQUEST_TS"]
        missed_trades_df.at[i, "STATUS"] = match["STATUS_CODE"]

# Save to output folder
with pd.ExcelWriter(output_path, engine="openpyxl", mode="w") as writer:
    pre_clearance_df.to_excel(writer, sheet_name="pre-clearance_trade", index=False)
    missed_trades_df.to_excel(writer, sheet_name="missed_trades_last2yrs", index=False)

print(f"✅ Matching complete. Output saved at: {output_path}")
