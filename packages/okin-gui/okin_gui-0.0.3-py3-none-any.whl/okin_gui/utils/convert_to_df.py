import pandas as pd

def load_file_to_df(file_path):
    # Check if the file is a CSV or Excel file based on the extension
    if file_path.endswith(".csv") or file_path.endswith(".txt"):
        try:
            # Read CSV file into a DataFrame
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return None
    elif file_path.endswith((".xls", ".xlsx")):
        try:
            # Read Excel file into a DataFrame
            df = pd.read_excel(file_path)
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return None
    else:
        print("Unsupported file format. Please provide a CSV or Excel file.")
        return None

    filtered_columns = [col for col in df.columns if not col.startswith('Unnamed')]
    df_filtered = df[filtered_columns]

    return df_filtered
