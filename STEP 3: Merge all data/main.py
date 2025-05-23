import pandas as pd
import json
import os

# get genre in string format 
with open('genre.json') as f:
    genre_to_str = json.load(f)

full_csv = pd.DataFrame()
full_json = dict()

# merge all batches
for filename in os.listdir('csv'):
    filepath = os.path.join('csv', filename)
    batch_csv = pd.read_csv(filepath, index_col=0)
    full_csv = pd.concat([full_csv, batch_csv], ignore_index=True)  # full_csv.append(batch_csv)

# parse string to list
full_csv['movie_genres'] = full_csv['movie_genres'].apply(
    lambda x: [int(i) for i in x.replace('[','').replace(']','').split()]
)
full_csv['poster_url'] = full_csv['poster_url'].apply(
    lambda x: [str(i).strip() for i in str(x).split(' ') if str(i[-4:]) == '.jpg']
)
full_csv['director'] = full_csv['director'].apply(
    lambda x: [str(i).replace('\'','').replace('\"','').strip() for i in str(x).replace('[','').replace(']','').split(',')]
)
full_csv['writer'] = full_csv['writer'].apply(
    lambda x: [str(i).replace('\'','').replace('\"','').strip() for i in str(x).replace('[','').replace(']','').split(',')]
)
full_csv['cast'] = full_csv['cast'].apply(
    lambda x: [str(i).replace('\'','').replace('\"','').strip() for i in str(x).replace('[','').replace(']','').split(',')]
)

# add genre in string format
full_csv['genre'] = full_csv['movie_genres'].apply(
    lambda genres: [genre_to_str[str(genre)] for genre in genres if str(genre) in genre_to_str.keys()]
)


# Update 'description' column based on 'storyline'
def merge_description(row):
    desc = str(row['description']).strip() if not pd.isna(row['description']) else ''
    story = str(row['storyline']).strip() if not pd.isna(row['storyline']) else ''

    if desc == story:
        return desc
    elif desc and story:
        return f"{desc} {story}"
    else:
        return desc or story


full_csv['description'] = full_csv.apply(merge_description, axis=1)

# save as csv
full_csv.to_csv('../movielens100k_details.csv', index=False)

exit()

# save as json
full_csv = full_csv.astype(object).where(pd.notna(full_csv), None)
# full_csv['rating'] = full_csv['rating'].apply(lambda x: x if )
with open('../movielens100k_details.json', 'w') as f:
    json.dump(full_csv.to_dict('records'), f)
