import os
import json
import random
import time

import pandas as pd
from tqdm import tqdm

from scrapper import IMDBPage


def retry_missing_fields(df, page):
    """Retry fetching data where release_date or country is NaN."""
    updated_rows = []
    changed = False

    for idx, row in df.iterrows():
        if pd.isna(row.get("release_date")) or pd.isna(row.get("country")) or pd.isna(row.get("storyline")):
            try:
                result = page.get_details(row['movie_url'])
                for key, value in result.items():
                    if pd.isna(row.get(key)) and pd.notna(value):
                        row[key] = value
                        changed = True
                updated_rows.append(row)
                time.sleep(random.randint(1, 5))
            except Exception as e:
                print(f"Retry failed for index {idx}: {e}")
                updated_rows.append(row)
        else:
            updated_rows.append(row)

    return pd.DataFrame(updated_rows), changed


def main():
    page = IMDBPage()
    movielens_df = pd.read_csv('movielens_poster.csv')
    movielens = movielens_df.to_dict('records')

    batch_size = 50
    n_batch = (len(movielens_df) // batch_size) + 1

    for batch in tqdm(range(n_batch), position=0):
        json_path = f'json/movielens100k_details_batch_{batch}.json'
        csv_path = f'csv/movielens100k_details_batch_{batch}.csv'

        if os.path.isfile(json_path) and os.path.isfile(csv_path):
            # Reload existing batch
            with open(json_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)

            # Retry for NaNs
            df, changed = retry_missing_fields(df, page)

            if changed:
                print(f"Updated missing fields in batch {batch}")
                with open(json_path, 'w') as f:
                    json.dump(df.to_dict('records'), f)
                df.to_csv(csv_path, index=False)

            continue  # Skip to next batch

        # First time scraping this batch
        movielens_batch = []

        for i, row in enumerate(tqdm(movielens[batch * batch_size: (batch + 1) * batch_size], position=1, leave=False)):
            try:
                result = page.get_details(row['movie_url'])
                row = dict(row)
                row.update(result)
                movielens_batch.append(row)
                time.sleep(random.randint(1, 8))
            except Exception as e:
                print(f'{batch * batch_size + i} - caught on main: {e}')

        # Save
        with open(json_path, 'w') as f:
            json.dump(movielens_batch, f)

        movielens_batch_df = pd.DataFrame(movielens_batch)
        movielens_batch_df.to_csv(csv_path, index=False)


if __name__ == '__main__':
    main()
