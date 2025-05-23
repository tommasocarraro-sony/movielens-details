import os
import pandas as pd

csv_folder = './STEP 3: Merge all data/csv'

for filename in os.listdir(csv_folder):
    csv_path = os.path.join(csv_folder, filename)

    # Read both dataframes
    main_df = pd.read_csv(csv_path, index_col=0)
    main_df = main_df.drop(columns=['release_date_y', 'country_y'])
    main_df = main_df.rename(columns={
        'release_date_x': 'release_date',
        'country_x': 'country'
    })

    # Overwrite the original file
    main_df.to_csv(csv_path)

    print(f"Updated: {filename}")