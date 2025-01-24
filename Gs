import pandas as pd
import os

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

def main():
    input_file = './input/your_file.xlsx'  # Replace with the actual file name
    output_file = './output/output_file.txt'
    config_file = './config.txt'
    
    # Ensure output directory exists
    os.makedirs('./output', exist_ok=True)

    # Load config
    config = load_config(config_file)
    password = config.get('password')
    if not password:
        print("Error: Password not found in config file.")
        return

    # Load Excel file
    try:
        df = pd.read_excel(input_file, header=None, engine='openpyxl', password=password)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Edge case: check if file is empty or has fewer rows than needed
    if df.empty or len(df) < 2:
        print("Error: Excel file must have at least two rows (header and footer).")
        return

    # Extract first and last rows
    first_row = df.iloc[0]
    last_row = df.iloc[-1]

    # Process the middle rows
    middle_rows = df.iloc[1:-1]
    columns_to_format = [2, 5, 10]  # Columns C, F, and K (zero-indexed)

    # Convert numeric columns and format rows
    def format_row(row):
        for col in columns_to_format:
            if col < len(row):
                # Convert float to string with comma as decimal separator
                if isinstance(row[col], (float, int)):
                    row[col] = f"{row[col]:.2f}".replace('.', ',')
        return ';'.join(map(str, row))

    processed_rows = middle_rows.apply(format_row, axis=1)

    # Write to output file
    with open(output_file, 'w') as f:
        f.write(';'.join(map(str, first_row)) + '\n')  # Write first row
        f.writelines(processed_rows.apply(lambda x: x + '\n'))  # Write processed rows
        f.write(';'.join(map(str, last_row)) + '\n')  # Write last row

    print(f"File processed successfully. Output saved to: {output_file}")

if __name__ == "__main__":
    main()
