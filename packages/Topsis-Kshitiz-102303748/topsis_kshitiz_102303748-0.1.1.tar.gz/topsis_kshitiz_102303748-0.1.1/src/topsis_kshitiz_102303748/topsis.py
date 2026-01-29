import sys
import pandas as pd
import numpy as np
import os

def encode_categorical_column(df, col):
    """Convert categorical column to numerical if possible."""
    unique_vals = df[col].unique()

    ordinal_mappings = {
        'low': 1, 'medium': 2, 'high': 3,
        'poor': 1, 'average': 2, 'good': 3, 'excellent': 4,
        'bad': 1, 'ok': 2, 'great': 3,
        'small': 1, 'large': 2,
        'yes': 1, 'no': 0
    }

    lower_vals = [str(v).lower() for v in unique_vals]
    if any(val in ordinal_mappings for val in lower_vals):
        mapping = {val: ordinal_mappings.get(str(val).lower(), 0) for val in unique_vals}
        return df[col].map(mapping)

    return pd.factorize(df[col])[0] + 1


def validate_and_prepare_data(args):
    if len(args) != 5:
        print("Error: Incorrect number of parameters.")
        print("Usage: python <program.py> <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        sys.exit(1)

    input_file, weights_str, impacts_str, output_file = args[1], args[2], args[3], args[4]

    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"Error: Unable to read file. {str(e)}")
        sys.exit(1)

    if len(df.columns) < 3:
        print("Error: Input file must contain three or more columns.")
        sys.exit(1)

    for col in df.columns[1:]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                try:
                    print(f"Info: Converting categorical column '{col}' to numeric.")
                    df[col] = encode_categorical_column(df, col)
                except Exception:
                    print(f"Error: Column '{col}' contains non-numeric values that cannot be converted.")
                    sys.exit(1)

    try:
        weights = [float(w.strip()) for w in weights_str.split(',')]
    except Exception:
        print("Error: Weights must be numeric values separated by commas.")
        sys.exit(1)

    try:
        impacts = [i.strip() for i in impacts_str.split(',')]
    except Exception:
        print("Error: Impacts must be separated by commas.")
        sys.exit(1)

    num_criteria = len(df.columns) - 1

    if len(weights) != num_criteria or len(impacts) != num_criteria:
        print(f"Error: Number of weights and impacts must match number of criteria ({num_criteria}).")
        sys.exit(1)

    if not all(i in ['+', '-'] for i in impacts):
        print("Error: Impacts must be either '+' or '-'")
        sys.exit(1)

    return df, weights, impacts, output_file


def topsis(df, weights, impacts):
    data = df.iloc[:, 1:].values

    norms = np.sqrt((data ** 2).sum(axis=0))
    normalized = data / norms

    weighted = normalized * weights

    impacts_arr = np.array(impacts)
    ideal_best = np.where(impacts_arr == '+', weighted.max(axis=0), weighted.min(axis=0))
    ideal_worst = np.where(impacts_arr == '+', weighted.min(axis=0), weighted.max(axis=0))

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    scores = dist_worst / (dist_best + dist_worst)
    ranks = scores.argsort()[::-1].argsort() + 1

    return scores, ranks


def main():
    df, weights, impacts, output_file = validate_and_prepare_data(sys.argv)

    scores, ranks = topsis(df, weights, impacts)

    df['Topsis Score'] = np.round(scores, 2)
    df['Rank'] = ranks

    try:
        df.to_csv(output_file, index=False)
        print(f"Results saved to '{output_file}'")
    except Exception as e:
        print(f"Error: Unable to save results. {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
