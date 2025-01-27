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
        for col in columns_to_format:
            if col < len(row):  # Ensure column exists
                if isinstance(row[col], (float, int)):
                    row[col] = f"{row[col]:.2f}".replace('.', ',')
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
