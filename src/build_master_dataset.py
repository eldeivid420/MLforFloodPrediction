"""
Merges the incident dataset and the meteorological dataset using date as the main 
column to perform join.
This will create the final dataset that will be used for all the work.
"""

# Imports
import pandas as pd
import numpy as np
import os


# Save file in the selected path
script_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(script_dir, "..", "data", "processed", "DatasetMaster.csv")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)


# Get the two datasets to join
df_incidents = pd.read_csv('data/processed/IncidentsDataset.csv')
df_meteodata = pd.read_csv('data/raw/CdmxWeather.csv')


# Merge the datasets
def merging_datasets(df_weather, df_incidents):

  # We first compare that both time columns are mathematically equals
  df_weather['time'] = pd.to_datetime(df_weather['time'])
  df_incidents['time'] = pd.to_datetime(df_incidents['time'])

  # We also do the same approach with alcaldia columns
  df_weather['alcaldia'] = df_weather['alcaldia'].astype(str).str.strip().str.upper()
  df_incidents['alcaldia'] = df_incidents['alcaldia'].astype(str).str.strip().str.upper()

  filas_clima_original = len(df_weather)

  # merging datasets
  df_merged = pd.merge(df_weather, df_incidents, on=['alcaldia', 'time'], how='left')

  # We populate the empty records that have no incidents and severity
  # for incident, if 0 was a regular day
  df_merged['incident'] = df_merged['incident'].fillna(0).astype(int)

  # for severity, 0 if nothing happens
  df_merged['severidad'] = df_merged['severidad'].fillna(0).astype(int)

  # for incident type, create 'without incident'
  df_merged['tema_solicitud'] = df_merged['tema_solicitud'].fillna('SIN INCIDENTE')

  return df_merged

dataset_final = merging_datasets(df_meteodata, df_incidents)
dataset_final.to_csv(OUTPUT_PATH, index=False)

print("\n--- TELEMETRY REPORT ---")
print(f"Total rows fetched: {len(dataset_final)}")
print(f"Dataset saved as: {OUTPUT_PATH}")