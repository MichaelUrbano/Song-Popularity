import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
import tensorflow as tf
from tensorflow.keras import layers, models


# Load the SQLite database
con = sqlite3.connect("SongPop.db")
df = pd.read_sql_query("SELECT * FROM ratings", con)
con.close()

# Drop unimportant columns
df = df.drop(columns=["song_name", "key", "audio_mode", "time_signature"])

# Split the target and features
y = df["song_popularity"].astype(float)
X = df.drop(columns=["song_popularity"])

# Now contains only numberic features
numeric_cols = list(X.columns)

# Preprocess
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_cols),
    ],
    remainder="drop"
)

X_processed = preprocessor.fit_transform(X)
X_processed = X_processed.astype(np.float32)
y = y.astype(np.float32)

X_train, X_val, y_train, y_val = train_test_split(
    X_processed, y, test_size=0.2, random_state=42
)

# Create the model
input_dim = X_train.shape[1]

model = models.Sequential([
    layers.Dense(64, activation="relu", input_shape=(input_dim,)),
    layers.Dropout(0.2),
    layers.Dense(64, activation="relu"),
    layers.Dropout(0.2),
    layers.Dense(1)
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="mse",
    metrics=["mae"]
)

model.summary()

# Train the model
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=50,
    batch_size=32,
    verbose=1
)

# Evaluate the model
loss, mae = model.evaluate(X_val, y_val, verbose=0)
print(f"Validation MAE: {mae}")

# Prediction
pred = model.predict(X_val[:5])
print("Predictions (first 5 validation samples):")
print(pred)
