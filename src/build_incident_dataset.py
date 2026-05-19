"""
Builds the incident dataset using the 3 different dataset for each category:
    - Mantenimiento drenaje
    - Mantenimiento alcantarilla
    - Fuga de agua
Each file can be downloaded from the following site:
https://tablero311.cdmx.gob.mx/#

The downloaded data is slightly transformed, some missing values within alcaldia
were rescued if there was zipcode, otherwise it was dropped. Also all empty
values were dropped, and time was rounded down to contain only hourly records.
"""

# Imports
import pandas as pd

# Path to save file
OUTPUT_PATH = "../data/raw/IncidentsDataset.csv"

# Get all csv into dataframes
df_mantenimiento_drenaje = pd.read_csv('../data/raw/MantenimientoDrenaje.csv')
df_mantenimiento_alcantarilla = pd.read_csv('../data/raw/MantenimientoAlcantarilla.csv')
df_fuga_de_agua = pd.read_csv('../data/raw/FugaDeAgua.csv',  encoding='latin-1')

# Only works with geographical columns (dimension on which we'll join datasets)
required_columns = [
        'fecha_solicitud',
        'hora_solicitud',
        'tema_solicitud',
        'colonia_solicitud',
        'alcaldia_solicitud',
        'codigo_postal_solicitud',
        'latitud',
        'longitud']


def only_geographical_columns(dataset):
  actual_columns = [col for col in required_columns if col in dataset.columns]
  adjusted_df = dataset[actual_columns].copy()
  return adjusted_df

# Applied to each dataset
df_mantenimiento_drenaje_adjusted = only_geographical_columns(df_mantenimiento_drenaje)
df_mantenimiento_alcantarilla_adjusted = only_geographical_columns(df_mantenimiento_alcantarilla)
df_fuga_de_agua_adjusted = only_geographical_columns(df_fuga_de_agua)


# Clean geographical null valies
def clean_geographicall_nulls(dataset):
  df = dataset.copy()

  # Check the nulls
  text_columns = ['colonia_solicitud', 'alcaldia_solicitud', 'codigo_postal_solicitud']
  for col in text_columns:
    df[col] = df[col].astype(str).str.strip()
    df[col] = df[col].replace(['','nan','NAN','NA','NaN','Nan','None','none'], np.nan)

  # Check for coordinates
  df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
  df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')

  items_before = len(df)

  # Check if we can identify the municipality using "alcaldia", "colonia" or zip code
  checkIfNull = (
        df['colonia_solicitud'].isna() &
        df['alcaldia_solicitud'].isna() &
        df['codigo_postal_solicitud'].isna() &
        (df['latitud'].isna() | df['longitud'].isna())
    )
  # ~: to keep only those values that we care fore
  clean_dataset = df[~checkIfNull].copy()

  items_after = len(clean_dataset)
  deleted_items = items_before - items_after

  print(f"--- Geo Data Dropped ---")
  print(f"Original records: {items_before}")
  print(f"Deleted records: {deleted_items}")
  print(f"Remaining records: {items_after}")

  return clean_dataset

df_mantenimiento_drenaje_cleaned = clean_geographicall_nulls(df_mantenimiento_drenaje_adjusted)
df_mantenimiento_alcantarilla_cleaned = clean_geographicall_nulls(df_mantenimiento_alcantarilla_adjusted)
df_fuga_de_agua_cleaned = clean_geographicall_nulls(df_fuga_de_agua_adjusted)


# Fill municipalities using zipcode
def fill_municipalities(dataset):

  #Create the new column, empty for the moment
  dataset['alcaldia'] = pd.Series(dtype='object')

  # Dictionary to use in the municipalities
  map_zipcode_municipality = {
        '01': 'ALVARO OBREGON', '02': 'AZCAPOTZALCO', '03': 'BENITO JUAREZ',
        '04': 'COYOACAN', '05': 'CUAJIMALPA DE MORELOS', '06': 'CUAUHTEMOC',
        '07': 'GUSTAVO A. MADERO', '08': 'IZTACALCO', '09': 'IZTAPALAPA',
        '10': 'MAGDALENA CONTRERAS', '11': 'MIGUEL HIDALGO', '12': 'MILPA ALTA',
        '13': 'TLAHUAC', '14': 'TLALPAN', '15': 'VENUSTIANO CARRANZA',
        '16': 'XOCHIMILCO'
    }

  # Get the zipcode first two digits to assign a municipality
  zipcode_prefix = (dataset['codigo_postal_solicitud']
                    .astype(str)
                    .str.extract(r'(\d+)', expand=False)
                    .fillna('')
                    .str.zfill(5)
                    .str[:2]
                  )

  # Map the zipcode using the dictionary
  mapped_municipalities = zipcode_prefix.map(map_zipcode_municipality)

  # Assign them to the new alcaldia column
  dataset.loc[mapped_municipalities.notna(), 'alcaldia'] = mapped_municipalities

  # Statistics
  total = len(dataset)
  municipality_assigned = dataset['alcaldia'].notna().sum()
  municipality_ommited = dataset['alcaldia'].isna().sum()
  print(f"Evaluated records: {total}")
  print(f"Assgined municipality to: {municipality_assigned}")
  print(f"Empty records: {municipality_ommited}") # to be checked with lat/long

  return dataset

df_mantenimiento_alcantarilla_filled = fill_municipalities(df_mantenimiento_alcantarilla_cleaned)
df_mantenimiento_drenaje_filled = fill_municipalities(df_mantenimiento_drenaje_cleaned)
df_fuga_de_agua_filled = fill_municipalities(df_fuga_de_agua_cleaned)


# Drop all records that does not contains municipality
def clean_empty_municipalities(dataset):
  length = len(dataset)

  # drop all records that does not have a municipality assigned
  df_final = dataset.dropna(subset=['alcaldia']).copy()

  final = len(df_final)
  deleted = length - final

  print(f"--- Municipality Dropped ---")
  print(f"Original records: {length}")
  print(f"Deleted records: {deleted}")

  return df_final

df_final_mantenimiento_drenaje = clean_empty_municipalities(df_mantenimiento_drenaje_filled)
df_final_mantenimiento_alcantarilla = clean_empty_municipalities(df_mantenimiento_alcantarilla_filled)
df_final_fuga_de_agua = clean_empty_municipalities(df_fuga_de_agua_filled)


# Drop all variables that does not give any usefull information
columns_to_preserve = ['fecha_solicitud', 'hora_solicitud', 'tema_solicitud', 'alcaldia']
# Note: preserve latitud and longitud if can track the location
columns_to_drop = ['colonia_solicitud', 'alcaldia_solicitud', 'codigo_postal_solicitud', 'latitud', 'longitud']

df_final_mantenimiento_drenaje.drop(columns_to_drop, axis=1, inplace=True)
df_final_mantenimiento_alcantarilla.drop(columns_to_drop, axis=1, inplace=True)
df_final_fuga_de_agua.drop(columns_to_drop, axis=1, inplace=True)


# Merge 3 datasets into a unique dataset with all the incidents
df_incidents = pd.concat([
    df_final_mantenimiento_drenaje,
    df_final_mantenimiento_alcantarilla,
    df_final_fuga_de_agua
], ignore_index=True)


# Round down the time to contain only hourly records
# Round down time
def round_down_time(dataset):
    df = dataset.copy()

    time_serie = pd.to_datetime(df['fecha_solicitud'] + ' ' + df['hora_solicitud'].astype(str), errors='coerce')
    df['time'] = time_serie

    # truncate time
    df['time'] = df['time'].dt.floor('h')

    columns_to_drop = ['fecha_solicitud', 'hora_solicitud']
    df.drop(columns_to_drop, axis=1, inplace=True)

    return df

df_incidents_rounded = round_down_time(df_incidents)


# Add flag to divide :
# 1: for incident reported
# 0: No incident reported
def add_incident_flag(dataset):
  df = dataset.copy()
  initial_rows = len(dataset)

  # group by incidents, if same happens, increase severity
  df_compressed = df.groupby(['alcaldia', 'time', 'tema_solicitud']).size().reset_index(name='severidad')

  # Compress exact hour incidents, if same type happens, then increase the severity
  df_compressed['incident'] = 1

  final_rows = len(df_compressed)
  duplicates_crushed = initial_rows - final_rows

  print(f"Redundant duplicates compressed: {duplicates_crushed:,}")
  print(f"Clean, unique incident hours: {final_rows:,}")

  return df_compressed
df_incidents_master = add_incident_flag(df_incidents_rounded)


# Save the dataset
df_incidents_master.to_csv(OUTPATH, index = False)

print("\n--- INCIDENT REPORT ---")
print(f"Total rows fetched: {len(df_incidents_master)}")
print(f"Dataset saved as: {OUTPUT_PATH}")
