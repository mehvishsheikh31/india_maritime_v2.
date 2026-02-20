import pandas as pd
import os

def merge_identity():
    print("🔗 Starting Bulletproof Identity Merger...")
    
    activity_path = 'data/processed/india_2024_mmsi_combined.parquet'
    registry_path = 'data/raw/fishing-vessels-v3.csv'
    output_path = 'data/processed/india_v2_final.parquet'

    if not os.path.exists(activity_path):
        print(f"❌ Error: {activity_path} not found.")
        return

    # 1. LOAD DATA
    df_activity = pd.read_parquet(activity_path)
    df_registry = pd.read_csv(registry_path, low_memory=False)

    # 2. FIND MMSI COLUMN
    reg_mmsi_col = next((c for c in df_registry.columns if c.lower() == 'mmsi'), None)
    if not reg_mmsi_col:
        print(f"❌ Could not find MMSI. Columns are: {df_registry.columns.tolist()}")
        return

    # 3. PREPARE REGISTRY (Safe Selection)
    # We will try to find Name, Flag, and Type, but won't crash if they are missing
    name_col = next((c for c in df_registry.columns if 'name' in c.lower()), None)
    flag_col = next((c for c in df_registry.columns if 'flag' in c.lower()), None)
    type_col = next((c for c in df_registry.columns if 'class' in c.lower() or 'type' in c.lower()), None)

    selected_cols = {reg_mmsi_col: 'MMSI'}
    if name_col: selected_cols[name_col] = 'VesselName'
    if flag_col: selected_cols[flag_col] = 'Flag'
    if type_col: selected_cols[type_col] = 'VesselType'

    registry_subset = df_registry[list(selected_cols.keys())].copy()
    registry_subset = registry_subset.rename(columns=selected_cols)

    # 4. JOIN
    df_activity['MMSI'] = df_activity['MMSI'].astype(str)
    registry_subset['MMSI'] = registry_subset['MMSI'].astype(str)
    registry_subset = registry_subset.drop_duplicates(subset=['MMSI'])
    
    final_df = pd.merge(df_activity, registry_subset, on='MMSI', how='left')

    # 5. SAFE FILL (Only fill if column exists)
    if 'VesselName' in final_df.columns:
        final_df['VesselName'] = final_df['VesselName'].fillna("Unknown Vessel")
    else:
        # Create a default name using the MMSI
        final_df['VesselName'] = "Vessel-" + final_df['MMSI']

    if 'Flag' in final_df.columns:
        final_df['Flag'] = final_df['Flag'].fillna("Unknown")
    else:
        final_df['Flag'] = "Unknown"

    if 'VesselType' in final_df.columns:
        final_df['VesselType'] = final_df['VesselType'].fillna("Unknown")
    else:
        final_df['VesselType'] = "Unknown"

    # 6. SAVE
    final_df.to_parquet(output_path, index=False)
    print(f"✨ SUCCESS! Saved to {output_path}")
    print(f"🚢 Unique Vessels: {final_df['MMSI'].nunique()}")

if __name__ == "__main__":
    merge_identity()