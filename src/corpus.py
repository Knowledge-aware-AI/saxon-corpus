import pandas as pd
import numpy as np

def combine_consecutive_rows(df):
    """
    Sequentially combine consecutive rows with identical metadata.
    
    Parameters:
    df (DataFrame): Your input DataFrame
    
    Returns:
    DataFrame: New DataFrame with combined rows
    """
    if df.empty:
        return df
    
    # Initialize result list
    result_rows = []
    
    # Start with the first row
    current_row = df.iloc[0].copy()
    current_saxon = []  # Store Saxon sentences as a list
    
    # Process remaining rows
    for i in range(1, len(df)):
        row = df.iloc[i]
        
        # Helper function to safely compare values (handles NaN)
        def safe_compare(val1, val2):
            # If both are NaN, they're considered equal
            if pd.isna(val1) and pd.isna(val2):
                return True
            # If only one is NaN, they're different
            if pd.isna(val1) or pd.isna(val2):
                return False
            # Both are not NaN, compare normally
            return val1 == val2
        
        # Check if current row has the same metadata as previous row
        if (safe_compare(row['Webpage'], current_row['Webpage']) and
            safe_compare(row['Date'], current_row['Date']) and
            safe_compare(row['Source'], current_row['Source']) and
            safe_compare(row['Origin'], current_row['Origin']) and
            safe_compare(row['Year'], current_row['Year'])):
            
            # Same metadata - add to current Saxon sentences
            saxon_value = row['Saxon']
            if pd.notna(saxon_value):  # Only add non-NaN values
                current_saxon.append(str(saxon_value))
        else:
            # Different metadata - save current combined row and start new one
            current_row['Saxon'] = ' '.join(current_saxon)
            result_rows.append(current_row)
            
            # Start new combination with current row
            current_row = row.copy()
            current_saxon = []
            saxon_value = row['Saxon']
            if pd.notna(saxon_value):  # Only add non-NaN values
                current_saxon.append(str(saxon_value))
    
    # Don't forget the last group
    current_row['Saxon'] = ' '.join(current_saxon)
    result_rows.append(current_row)

    # Create DataFrame and add length column
    result_df = pd.DataFrame(result_rows)
    result_df['length'] = result_df['Saxon'].str.len()
    
    return result_df.reset_index(drop=True)

def delete_entry(df, column, value, included=False):
    """ Delete rows from the DataFrame where the specified column matches the given value.
        If included is True, it will delete rows where the column contains the value as a substring."""
    if included:
        return df[~df[column].str.contains(value, na=False)]
    else:
        return df[df[column] != value]
    
def edit_entry(df, column, old_value, new_value, included=False):
    """ Edit rows in the DataFrame where the specified column matches the old_value and replace it with new_value.
        If included is True, it will edit rows where the column contains the old_value as a substring."""
    if included:
        df.loc[df[column].str.contains(old_value, na=False), column] = new_value
    else:
        df.loc[df[column] == old_value, column] = new_value
    return df

def corpus_details(csv_path="data.csv"):
    """Print details about the corpus."""
    df = pd.read_csv(csv_path)
    total_entries = len(df)
    total_saxon_length = df['length'].sum()
    total_parallel_length = int(df['German'].str.len().sum())
    unique_sources = df['Source'].nunique()
    unique_origins = df['Origin'].nunique()
    unique_years = df['Year'].nunique()
    
    print(f"Total entries: {total_entries}")
    print(f"Total Saxon length: {total_saxon_length}")
    print(f"Parallel data length: {total_parallel_length}")
    print(f"Unique sources: {unique_sources}")
    print(f"Unique origins: {unique_origins}")
    print(f"Unique years: {unique_years}")

if __name__ == "__main__":
    df = pd.read_csv("data.csv")
    #df = edit_entry(df, "Source", "Lene Voigt", "Lene Voigt", included=True)
    #print(df.loc[df["Source"].str.contains("Lene Voigt", case=False, na=False), "Source"])
    #print(df['Origin'].unique())
    corpus_details()