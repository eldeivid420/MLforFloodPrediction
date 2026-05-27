
import pandas as pd


def data_feature_selection(X_train, X_test):
    """
    Dropping the features that the EDA phase identified:
    Redundant Variables: Those that are highly correlated (>0.90) and will cause multicollinearity issues in Logistic Regression
    
    Also we are dropping features that cause data leakage or are metadata that would crash the matrix
    """

    leakage_features = [
        'severidad',      
        'tema_solicitud',  
        'runoff'          
    ]

    redundant_features = [
        'soil_moisture_0_to_7cm_mean_3h',
        'soil_moisture_0_to_7cm_mean_6h',
        'soil_moisture_0_to_7cm_mean_12h',
        'soil_moisture_0_to_7cm_mean_24h',
        'soil_moisture_7_to_28cm_mean_3h',
        'soil_moisture_7_to_28cm_mean_6h',
        'soil_moisture_7_to_28cm_mean_12h',
        'soil_moisture_7_to_28cm_mean_24h'
    ]
    
    # Single list to drop
    total_cols_to_drop = leakage_features + redundant_features
    

    # Execute the Drop on BOTH partitions simultaneously to guarantee matrix alignment
    X_train_clean = X_train.drop(columns=total_cols_to_drop)
    X_test_clean = X_test.drop(columns=total_cols_to_drop)
    
    print(f"Original Feature Count: {X_train.shape[1]}")
    print(f"Cleaned Feature Count:  {X_train_clean.shape[1]}")
    
    return X_train_clean, X_test_clean


def split_data(df, split_date='2025-01-01'):

  # One-Hot Encoding the categorical variable for alcaldia
  df_encoded = pd.get_dummies(df, columns=['alcaldia'], drop_first=False, dtype=int)

  # Slicing using the split date
  df_encoded['time'] = pd.to_datetime(df_encoded['time'])

  # Masks to split train and test
  train_mask = df_encoded['time'] < split_date
  test_mask = df_encoded['time'] >= split_date

  # make the splitting of the data
  df_train = df_encoded[train_mask].copy()
  df_test = df_encoded[test_mask].copy()

  # Delete features from train
  columns_to_drop = ['incident', 'time']

  X_train = df_train.drop(columns=columns_to_drop)
  y_train = df_train['incident']

  X_test = df_test.drop(columns=columns_to_drop)
  y_test = df_test['incident']

  return X_train, X_test, y_train, y_test


def split_data_3way(df):
    """
    Splits the data in 3 chronological splits:
    - Train: Before 2024-01-01
    - Validation: 2024-01-01 to 2024-12-31
    - Test: 2025-01-01 up to the end
    """
    # One-Hot Encoding
    df_encoded = pd.get_dummies(df, columns=['alcaldia'], drop_first=False, dtype=int)
    df_encoded['time'] = pd.to_datetime(df_encoded['time'])

    # Chronological Masks
    train_mask = df_encoded['time'] < '2024-01-01'
    val_mask   = (df_encoded['time'] >= '2024-01-01') & (df_encoded['time'] < '2025-01-01')
    test_mask  = df_encoded['time'] >= '2025-01-01'

    # Target Extraction
    y_train = df_encoded.loc[train_mask, 'incident'].values
    y_val   = df_encoded.loc[val_mask, 'incident'].values
    y_test  = df_encoded.loc[test_mask, 'incident'].values

    #Feature Isolation
    X_train_raw = df_encoded.loc[train_mask].copy()
    X_val_raw   = df_encoded.loc[val_mask].copy()
    X_test_raw  = df_encoded.loc[test_mask].copy()

    return X_train_raw, X_val_raw, X_test_raw, y_train, y_val, y_test



def data_feature_selection_3way(X_train, X_val, X_test):
    """
    Drops unwanted or unused features from the 3-way split datasets
    """
    leakage_features = ['incident', 'time', 'severidad', 'tema_solicitud', 'runoff']
    redundant_features = [
        'soil_moisture_0_to_7cm_mean_3h', 'soil_moisture_0_to_7cm_mean_6h',
        'soil_moisture_0_to_7cm_mean_12h', 'soil_moisture_0_to_7cm_mean_24h',
        'soil_moisture_7_to_28cm_mean_3h', 'soil_moisture_7_to_28cm_mean_6h',
        'soil_moisture_7_to_28cm_mean_12h', 'soil_moisture_7_to_28cm_mean_24h'
    ]
    master_drop_list = leakage_features + redundant_features

    cols_to_drop = [col for col in master_drop_list if col in X_train.columns]

    X_train_clean = X_train.drop(columns=cols_to_drop)
    X_val_clean   = X_val.drop(columns=cols_to_drop)
    X_test_clean  = X_test.drop(columns=cols_to_drop)

    return X_train_clean, X_val_clean, X_test_clean