import pandas as pd
import numpy as np
import re

# --- 1. Load Data ---
file_name = "ICRISAT-District Level Data - ICRISAT-District Level Data.csv"
df = pd.read_csv(file_name)

# --- 2. Define Column Cleaning Function ---
def clean_col_name(col_name):
    """
    Standardizes column names to snake_case, removes units,
    and handles specific naming patterns.
    """
    col_name = col_name.lower().strip()
    # Replace unit indicators with a standardized suffix
    col_name = re.sub(r'\(1000 ha\)', '_area_1000ha', col_name)
    col_name = re.sub(r'\(1000 tons\)', '_production_1000tons', col_name)
    col_name = re.sub(r'\(kg per ha\)', '_yield_kg_per_ha', col_name)
    col_name = re.sub(r'[()\.]', '', col_name) # Remove remaining parentheses and dots
    col_name = re.sub(r'\s+', '_', col_name)   # Replace spaces with underscores
    col_name = re.sub(r'_-_', '_', col_name)   # Clean up potential double underscores from hyphen
    return col_name

# Apply the column name cleaning function
df.columns = [clean_col_name(col) for col in df.columns]

# --- 3. Handle Sentinel Values and Duplicates ---

# Identify numerical columns for sentinel value replacement
numerical_cols = df.select_dtypes(include=np.number).columns.tolist()

# Replace sentinel value -1.0 with NaN in all numerical columns
df[numerical_cols] = df[numerical_cols].replace(-1.0, np.nan)

# Remove duplicates if any were found
df.drop_duplicates(inplace=True)

# --- 4. Define Yield Triples and Imputation Logic ---

# Identify all 'yield' columns
yield_cols = [col for col in df.columns if 'yield_kg_per_ha' in col]

# List of (yield, production, area) column triples
yield_triples = []
for yield_col in yield_cols:
    base_name = yield_col.replace('_yield_kg_per_ha', '')
    area_col = base_name + '_area_1000ha'
    production_col = base_name + '_production_1000tons'
    if area_col in df.columns and production_col in df.columns:
        yield_triples.append((yield_col, production_col, area_col))

# Impute area and production NaNs with 0
area_production_cols = [col for col in df.columns if '_area_1000ha' in col or '_production_1000tons' in col]
df[area_production_cols] = df[area_production_cols].fillna(0)

# Impute non-crop related area columns (assuming missing means zero)
non_crop_area_cols = [
    'fruits_area_area_1000ha',
    'vegetables_area_area_1000ha',
    'fruits_and_vegetables_area_area_1000ha',
    'potatoes_area_area_1000ha',
    'onion_area_area_1000ha',
    'fodder_area_area_1000ha'
]
# Robust handling: some datasets may have slightly different column names
# (e.g., 'fruits_area_1000ha' instead of 'fruits_area_area_1000ha').
# For any expected non-crop area column, try to find an existing matching
# column, attempt simple name fixes, or create the missing column with 0s.
fixed_cols = []
mapped = {}
for col in non_crop_area_cols:
    if col in df.columns:
        fixed_cols.append(col)
        continue

    # Try simple fixes: collapse duplicated 'area' or fix repeated parts
    candidate = col.replace('area_area', 'area')
    if candidate in df.columns:
        fixed_cols.append(candidate)
        mapped[col] = candidate
        continue

    # Fallback: try to find any column that contains the main keyword and is an area column
    # Extract prefix before the first '_area'
    prefix = col.split('_area')[0]
    found = None
    for existing_col in df.columns:
        if prefix in existing_col and '_area_1000ha' in existing_col:
            found = existing_col
            break
    if found:
        fixed_cols.append(found)
        mapped[col] = found
        continue

    # If still not found, create the missing column with zeros
    df[col] = 0
    fixed_cols.append(col)

if mapped:
    print('Non-crop area columns mapped to existing columns:', mapped)

# Finally, fill NaNs with 0 for the resolved set of columns
df[fixed_cols] = df[fixed_cols].fillna(0)

# --- 5. Final Yield Recalculation after Imputing Area/Production ---

# Recalculate yield for any remaining NaN values using the imputed areas/productions.
# Yield (kg/ha) = (Production (1000 tons) / Area (1000 ha)) * 1000
for yield_col, production_col, area_col in yield_triples:
    # Condition 1: Recalculate if yield is NaN and area is non-zero
    recalc_condition = df[yield_col].isna() & (df[area_col] != 0)
    df.loc[recalc_condition, yield_col] = (df[production_col] / df[area_col]) * 1000

    # Condition 2: Set yield to 0 if yield is NaN and area is 0
    zero_yield_condition = df[yield_col].isna() & (df[area_col] == 0)
    df.loc[zero_yield_condition, yield_col] = 0

# --- 6. Save Cleaned Data ---
cleaned_file_name = "ICRISAT_District_Level_Data_Cleaned.csv"
df.to_csv(cleaned_file_name, index=False)
print(f"Cleaned data saved to {cleaned_file_name}")

# Display the final info (optional, for verification)
print("\nFinal DataFrame Info:")
df.info()