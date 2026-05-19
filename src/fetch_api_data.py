"""
Fetches meteorological and climatological telemetry data using the Open-Meteo API.

This module retrieves weather-related variables such as temperature,
precipitation, humidity, wind conditions, and other environmental
features used for flood prediction and analysis.

Weather data is provided by Open-Meteo:
https://open-meteo.com/

The generated data is stored locally to avoid repeated API calls during
the main execution pipeline and to improve reproducibility.
"""

import requests
import pandas as pd
import time

OUTPUT_PATH = "../data/raw/CdmxWeather2.csv"

# Municipalities coordinates
alcaldias = {
    "ALVARO OBREGON": [19.35, -99.22], "AZCAPOTZALCO": [19.48, -99.18],
    "BENITO JUAREZ": [19.38, -99.16], "COYOACAN": [19.33, -99.16],
    "CUAJIMALPA DE MORELOS": [19.33, -99.28], "CUAUHTEMOC": [19.43, -99.14],
    "GUSTAVO A. MADERO": [19.49, -99.11], "IZTACALCO": [19.39, -99.09],
    "IZTAPALAPA": [19.34, -99.04], "MAGDALENA CONTRERAS": [19.30, -99.24],
    "MIGUEL HIDALGO": [19.43, -99.19], "MILPA ALTA": [19.19, -99.02],
    "TLAHUAC": [19.28, -99.00], "TLALPAN": [19.22, -99.17],
    "VENUSTIANO CARRANZA": [19.43, -99.09], "XOCHIMILCO": [19.25, -99.10]
}

START_DATE = "2019-01-01"
END_DATE = "2026-01-31"
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
VARIABLES = [
    "temperature_2m",
    "precipitation",
    "relative_humidity_2m",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "soil_moisture_28_to_100cm",
    "et0_fao_evapotranspiration",
    "wind_speed_10m",
    "wind_gusts_10m"
]
VARIABLES_STRING = ",".join(VARIABLES)

dfs_weather = []

# building the dataset
for name, coords in alcaldias.items():
    print(f"Downloading: {name} ...", end = " ")
    params = {
        "latitude": coords[0],
        "longitude": coords[1],
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": VARIABLES_STRING,
        "timezone": "America/Mexico_City"
    }
    try:
      response = requests.get(BASE_URL, params=params)
      data = response.json()

      if "hourly" in data:
        # dump json into dataframe
        df_temp = pd.DataFrame(data["hourly"])
        df_temp["alcaldia"] = name

        dfs_weather.append(df_temp)
        print(f"{len(df_temp)} hours recorded")

      else:
        print(f"ERROR: {data.get('reason', 'Unknown error')}")

    except Exception as e:
      print(f"Failed to fetch data for {name}: {e}")

    time.sleep(65)

    print("\nAssembling the Master Matrix...")
df_weather_master = pd.concat(dfs_weather, ignore_index=True)

# Convert the string time to a real mathematical datetime object
df_weather_master['time'] = pd.to_datetime(df_weather_master['time'])

# Save final dataset
df_weather_master.to_csv(OUTPUT_PATH, index=False)

print("\n--- TELEMETRY REPORT ---")
print(f"Total rows fetched: {len(df_weather_master)}")
print(f"Dataset saved as: {OUTPUT_PATH}")