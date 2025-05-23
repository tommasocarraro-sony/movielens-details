import os
import pandas as pd

metadata_folder = './STEP 2: Scrape Movie Details from IMDB/csv'
csv_folder = './STEP 3: Merge all data/csv'

for filename in os.listdir(csv_folder):
    csv_path = os.path.join(csv_folder, filename)
    meta_path = os.path.join(metadata_folder, filename)

    if not os.path.exists(meta_path):
        print(f"Metadata file missing for: {filename}, skipping.")
        continue

    # Read both dataframes
    main_df = pd.read_csv(csv_path, index_col=0)
    meta_df = pd.read_csv(meta_path, index_col=0)

    # Merge release_date and country into the main dataframe
    merged_df = main_df.merge(meta_df[['movie_id', 'release_date', 'country', 'storyline']], on="movie_id", how='left')

    # Overwrite the original file
    merged_df.to_csv(csv_path)

    print(f"Updated: {filename}")
