

import pandas as pd
import numpy as np
import os

# Read dataset (attempt to parse `time` if present)
dataset_final = pd.read_csv('data/processed/DatasetMaster.csv', parse_dates=['time'])

# Save file in the selected path
script_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(script_dir, "..", "data", "processed", "DatasetMaster.csv")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)


def feature_engineering(dataset):

  df = dataset.copy()

  # Ensure 'time' is datetimelike before using .dt
  df['time'] = pd.to_datetime(df['time'], errors='coerce')
  df = df.dropna(subset=['time']).copy()
  # Sort time series chronologically by municipality
  df = df.sort_values(by=['alcaldia', 'time']).reset_index(drop=True)

  # Temporal deconstruction from YYYY-DD-MM HH:MM:SS into 4 columns
  df['mes'] = df['time'].dt.month
  df['dia_semana'] = df['time'].dt.dayofweek # Monday=0, Sunday=6
  df['hora_del_dia'] = df['time'].dt.hour
  df['es_fin_de_semana'] = df['dia_semana'].apply(lambda x: 1 if x >= 5 else 0)

  # Creating rolling windows to take accumulate precipitation for 3, 6 12 and 24 hours
  # Variable that accumulate rain
  col_to_sum = ['precipitation']

  # Variables that saturate (Soil Moisture, Humidity)
  cols_to_mean = ['soil_moisture_0_to_7cm', 'soil_moisture_7_to_28cm', 'relative_humidity_2m']

  # Time rolling windows
  time_windows = [3, 6, 12, 24]

  for w in time_windows:
    for col in col_to_sum:
      if col in df.columns:
        df[f'{col}_sum_{w}h'] = df.groupby('alcaldia')[col].transform(lambda x: x.rolling(window=w, min_periods=1).sum())

    for col in cols_to_mean:
      if col in df.columns:
        df[f'{col}_mean_{w}h'] = df.groupby('alcaldia')[col].transform(lambda x: x.rolling(window=w, min_periods=1).mean())

  # Dropping the first 24 hours of data per municipality to calculate well the window
  df_final = df[df.groupby('alcaldia').cumcount() >= 24].reset_index(drop=True)

  print(f"Original rows: {len(df)}")
  print(f"Final rows after burn-in drop: {len(df_final)}")
  return df_final

df_ml = feature_engineering(dataset_final)
df_ml.to_csv(OUTPUT_PATH, index=False)
