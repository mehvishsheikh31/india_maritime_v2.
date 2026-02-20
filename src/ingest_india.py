import pandas as pd
import os
import glob

def process_mmsi_files():
    print("🚀 Starting Production Processing for GFW v3.0...")
    
    raw_folder = 'data/raw/'
    all_files = glob.glob(os.path.join(raw_folder, "mmsi-daily-*.csv"))
    processed_path = 'data/processed/india_2024_mmsi_combined.parquet'
    
    if not all_files:
        print(f"❌ Error: No files found in {raw_folder}")
        return

    india_chunks = []
    
    # Define the exact GFW v3.0 columns based on your output
    LAT_COL = 'cell_ll_lat'
    LON_COL = 'cell_ll_lon'
    TIME_COL = 'date'
    MMSI_COL = 'mmsi'

    for file_path in all_files:
        try:
            # We process 100k rows at a time for speed
            for chunk in pd.read_csv(file_path, chunksize=100000):
                
                # Check if coordinates are in degrees (0-90) or scaled (0-9000)
                # If the first value is > 1000, we divide by 100
                first_lat = chunk[LAT_COL].iloc[0]
                if abs(first_lat) > 500:
                    chunk[LAT_COL] = chunk[LAT_COL] / 100.0
                    chunk[LON_COL] = chunk[LON_COL] / 100.0

                # FILTER: India Region (Lat 5-25, Lon 65-95)
                mask = (chunk[LAT_COL].between(5, 25)) & (chunk[LON_COL].between(65, 95))
                subset = chunk[mask].copy()
                
                if not subset.empty:
                    # Rename to our standard names for the dashboard
                    subset = subset.rename(columns={
                        LAT_COL: 'LAT',
                        LON_COL: 'LON',
                        TIME_COL: 'BaseDateTime',
                        MMSI_COL: 'MMSI'
                    })
                    india_chunks.append(subset)
            
            print(f"✅ Processed: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"⚠️ Error in {os.path.basename(file_path)}: {e}")

    if india_chunks:
        print("📊 Consolidating results...")
        full_india_df = pd.concat(india_chunks, ignore_index=True)
        full_india_df['BaseDateTime'] = pd.to_datetime(full_india_df['BaseDateTime'])
        
        # Save the master file
        os.makedirs('data/processed', exist_ok=True)
        full_india_df.to_parquet(processed_path, index=False)
        print(f"✨ SUCCESS! Saved {len(full_india_df)} pings to {processed_path}")
    else:
        print("❌ No data found for India coordinates. Try widening the filter to (0-40, 40-110).")

if __name__ == "__main__":
    process_mmsi_files()