#!/usr/bin/env python3

import sqlite3
import re
import os
import joblib
import pandas as pd
import numpy as np

# Sklearn imports
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error

MODEL_FILENAME = "song_popularity_model.pkl"
DATABASE_FILENAME = "SongPop.db"

# 1. Load in dataset from database
print("Loading data from database...")
con = sqlite3.connect(DATABASE_FILENAME)

chords = pd.read_sql_query("""
    SELECT * FROM chords
    WHERE spotify_song_id IS NOT NULL;
""", con)

songs = pd.read_sql_query("""
    SELECT track_id, title, artist_name, artist_hotttnesss, artist_familiarity, duration, year
    FROM songs
    WHERE title IS NOT NULL;
""", con)

id_translations = pd.read_sql_query("""
    SELECT * FROM id_translations
    WHERE track_id IS NOT NULL;
""", con)

lyrics_raw = pd.read_sql_query("""
    SELECT track_id, word, count
    FROM lyrics
    WHERE is_test = 0
    AND track_id IN (SELECT track_id FROM songs)
""", con)
con.close()

# Processing lyrics
def create_lyric_string(group):
    return " ".join((group['word'] + " ") * group['count'])

print("Processing lyrics...")
lyrics_grouped = lyrics_raw.groupby('track_id')[['word', 'count']].apply(
    lambda x: " ".join((x['word'] + " ") * x['count'])
).reset_index(name='lyrics_text')

# 2. Join Tables
print("Merging data...")

# Normalize text for merging
songs['title_norm'] = songs['title'].str.lower().str.strip()
songs['artist_norm'] = songs['artist_name'].str.lower().str.strip()
id_translations['title_norm'] = id_translations['track_name'].str.lower().str.strip()
id_translations['artist_norm'] = id_translations['artist_name'].str.lower().str.strip()

# Merge chords to id_translations
merged1 = chords.merge(
    id_translations,
    left_on=['spotify_song_id', 'spotify_artist_id'],
    right_on=['track_id', 'artist_id'],
    how='inner'
)

# Merge songs (using suffixes to handle duplicate artist_name columns)
merged2 = merged1.merge(
    songs,
    left_on=['title_norm', 'artist_norm'],
    right_on=['title_norm', 'artist_norm'],
    how='inner',
    suffixes=('_remove', '')
)

# Merge lyrics
merged = merged2.merge(
    lyrics_grouped,
    left_on='track_id',
    right_on='track_id',
    how='left'
)

# Fill missing lyrics
merged['lyrics_text'] = merged['lyrics_text'].fillna("")

# 3. Feature Engineering

# A. Calculate Target
merged["synthetic_popularity"] = (
      0.6 * merged["artist_hotttnesss"].fillna(0)
    + 0.4 * merged["artist_familiarity"].fillna(0)
) * 100

# B. Clean Chords
def clean_chord_string(text):
    if text is None or not isinstance(text, str):
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    return text.strip()

merged['chords_clean'] = merged['chords'].apply(clean_chord_string)

# C. Define Feature Set
feature_columns = ["duration", "year", "chords_clean", "lyrics_text"]

cols_to_keep = ["title", "artist_name"] + feature_columns + ["synthetic_popularity"]
df = merged[cols_to_keep].dropna()

df_train, df_test = train_test_split(df, test_size=0.20, random_state=42)

X_train = df_train[feature_columns]
y_train = df_train["synthetic_popularity"]

X_test = df_test[feature_columns]
y_test = df_test["synthetic_popularity"]

# 4 & 5. Model Loading OR Training

if os.path.exists(MODEL_FILENAME):
    print(f"\nFound existing model '{MODEL_FILENAME}'. Loading...")
    best_model = joblib.load(MODEL_FILENAME)

else:
    print(f"\nNo model found at '{MODEL_FILENAME}'. Starting training...")

    # A. Pipeline Setup
    preprocess = ColumnTransformer(
        transformers=[
            ("chords", TfidfVectorizer(token_pattern=r"\S+", ngram_range=(1, 3), max_features=1000), "chords_clean"),
            ("lyrics", TfidfVectorizer(stop_words='english', max_features=1000), "lyrics_text"),
            ("num", "passthrough", ["duration", "year"])
        ]
    )

    pipeline = Pipeline(steps=[
        ("prep", preprocess),
        ("reg", GradientBoostingRegressor(random_state=42))
    ])

    # B. Hyperparameter Tuning
    print("Starting Hyperparameter Tuning...")

    param_dist = {
        'reg__n_estimators': [200, 300], 
        'reg__learning_rate': [0.1, 0.2],
        'reg__max_depth': [4, 5],
        'prep__chords__max_features': [500, 1000],
        'prep__lyrics__max_features': [500, 1000]
    }

    random_search = RandomizedSearchCV(
        pipeline, 
        param_distributions=param_dist, 
        n_iter=10, 
        cv=5, 
        n_jobs=-1, 
        verbose=1,
        scoring='neg_mean_absolute_error',
        random_state=42
    )

    random_search.fit(X_train, y_train)
    best_model = random_search.best_estimator_

    # C. Save
    joblib.dump(best_model, MODEL_FILENAME)
    print(f"Training complete. Model saved to '{MODEL_FILENAME}'.")


# 6. Evaluation

print("\nEvaluating model on Test Set...")
predictions = best_model.predict(X_test)
mae = mean_absolute_error(y_test, predictions)
r2 = best_model.score(X_test, y_test)

print("\n--- Model Performance ---")
print(f"R^2 Score: {r2:.4f}")
print(f"Mean Absolute Error (MAE): {mae:.2f}")

# Only try to print feature importance if the model supports it
if hasattr(best_model.named_steps['reg'], 'feature_importances_'):
    print("\n--- Top Features ---")
    prep = best_model.named_steps['prep']
    reg = best_model.named_steps['reg']

    # Get feature names from both vectorizers
    chord_names = prep.named_transformers_['chords'].get_feature_names_out()
    chord_names = ["CHORD_" + name for name in chord_names]

    lyric_names = prep.named_transformers_['lyrics'].get_feature_names_out()
    lyric_names = ["LYRIC_" + name for name in lyric_names]

    num_names = ["duration", "year"]

    all_names = np.concatenate([chord_names, lyric_names, num_names])
    importances = reg.feature_importances_
    indices = np.argsort(importances)[::-1]

    for i in range(50):
        idx = indices[i]
        print(f"{i+1}. {all_names[idx]} ({importances[idx]:.4f})")

# Test 30 Random Songs and Display Results
print("\n" + "="*80)
print("PREDICTING 30 RANDOM SONGS FROM TEST SET")
print("="*80)

# 1. Sample 30 random songs from the test dataframe
sample_df = df_test.sample(30, random_state=101)

# 2. Isolate X and y for this sample
X_sample = sample_df[feature_columns]
y_actual = sample_df["synthetic_popularity"].values

# 3. Predict
y_pred = best_model.predict(X_sample)

# 4. Print Table
print(f"{'Title':<35} | {'Artist':<25} | {'Actual':<6} | {'Pred':<6} | {'Diff':<6}")
print("-" * 90)

for i in range(len(sample_df)):
    title = sample_df.iloc[i]['title']
    artist = sample_df.iloc[i]['artist_name']
    actual = y_actual[i]
    pred = y_pred[i]
    diff = abs(actual - pred)

    # Truncate long titles so the table doesn't break
    title_fmt = (title[:32] + '..') if len(title) > 32 else title
    artist_fmt = (artist[:22] + '..') if len(artist) > 22 else artist

    print(f"{title_fmt:<35} | {artist_fmt:<25} | {actual:.1f}   | {pred:.1f}   | {diff:.1f}")