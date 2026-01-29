"""
Command line interface for TOPSIS.
"""

import sys
import pandas as pd

from topsis_siddharth.core import topsis
from topsis_siddharth.validation import (
    validate_file,
    load_and_validate_csv,
    parse_weights,
    parse_impacts
)


def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    try:
        validate_file(input_file)

        df = load_and_validate_csv(input_file)
        criteria_data = df.iloc[:, 1:].values

        n_criteria = criteria_data.shape[1]

        weights = parse_weights(weights_str, n_criteria)
        impacts = parse_impacts(impacts_str, n_criteria)

        scores, ranks = topsis(criteria_data, weights, impacts)

        df["Topsis Score"] = scores
        df["Rank"] = ranks

        df.to_csv(output_file, index=False)

        print(f"TOPSIS analysis completed. Results saved to '{output_file}'")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

