### models_atr_1 ###
- Columns Name
    - target_long_atr_1
    - target_short_atr_1

- Labels configurazione
    - horizon: 20
    - threshold: 0.002
    - k: 1.0

- Training parameters
    "objective": "binary",
    "learning_rate": 0.03,
    "num_leaves": 63,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "min_data_in_leaf": 50,
    "lambda_l1": 1.0,
    "lambda_l2": 1.0,
    "metric": "binary_logloss",
    "scale_pos_weight": scale_pos_weight,
    "verbosity": -1

- Other params
    num_boost_round=2000,
    valid_names=["valid"],
    callbacks=[lgb.early_stopping(stopping_rounds=100)]

- Threshold -> 0.20

================================================================================

### models_atr_2 ###
- Columns Name
    - target_long_atr_2
    - target_short_atr_2

- Labels configurazione
    - horizon: 10
    - threshold: 0.0005
    - k: 0.5

- Training parameters
    "objective": "binary",
    "learning_rate": 0.001,
    "num_leaves": 31,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "min_data_in_leaf": 20,
    "lambda_l1": 1.0,
    "lambda_l2": 1.0,
    "metric": "binary_logloss",
    "verbosity": -1