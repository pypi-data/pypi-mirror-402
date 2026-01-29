"""
Validation utilities for TOPSIS inputs.
"""

import os
import pandas as pd


def validate_file(path):
    if not os.path.isfile(path):
        raise FileNotFoundError("Input file does not exist")


def load_and_validate_csv(path):
    df = pd.read_csv(path)

    if df.shape[1] < 3:
        raise ValueError("Input file must contain at least 3 columns")

    criteria = df.iloc[:, 1:]

    # 1️⃣ Check for missing values
    if criteria.isnull().values.any():
        rows, cols = criteria.isnull().to_numpy().nonzero()
        col_name = criteria.columns[cols[0]]
        row_index = rows[0] + 2  # +2 for header and 0-index
        raise ValueError(
            f"Missing value detected at row {row_index}, column '{col_name}'"
        )

    # 2️⃣ Force numeric conversion
    for col in criteria.columns:
        try:
            pd.to_numeric(criteria[col])
        except ValueError:
            raise ValueError(
                f"Non-numeric value found in column '{col}'. "
                "Categorical values are not allowed."
            )

    return df


def parse_weights(weights_str, n_criteria):
    try:
        weights = list(map(float, weights_str.split(",")))
    except ValueError:
        raise ValueError("Weights must be numeric and comma-separated")

    if len(weights) != n_criteria:
        raise ValueError("Number of weights must match number of criteria")

    return weights


def parse_impacts(impacts_str, n_criteria):
    impacts = impacts_str.split(",")

    if len(impacts) != n_criteria:
        raise ValueError("Number of impacts must match number of criteria")

    for i in impacts:
        if i not in ["+", "-"]:
            raise ValueError("Impacts must be either '+' or '-'")

    return impacts
