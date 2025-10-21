import pandas as pd

# Load the messy CSV
df = pd.read_csv('data/results/pilot_deepseek.csv')

# Keep only rows that either:
# 1. Solved successfully, OR
# 2. Failed for reasons OTHER than the API key error
api_key_error = "'NoneType' object has no attribute 'get'"
df_clean = df[~df['error'].astype(str).str.contains(api_key_error, na=False)]

# Save cleaned version
df_clean.to_csv('data/results/pilot_deepseek_clean.csv', index=False)

print(f"Original rows: {len(df)}")
print(f"Cleaned rows: {len(df_clean)}")
print(f"Removed: {len(df) - len(df_clean)} bad rows")