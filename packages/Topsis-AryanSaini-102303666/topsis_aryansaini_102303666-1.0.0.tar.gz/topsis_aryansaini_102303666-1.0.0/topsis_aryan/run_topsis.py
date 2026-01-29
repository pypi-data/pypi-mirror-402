import sys
import pandas as pd
import os
from math import sqrt

def calculate_topsis(data, weights, impacts):
    data_numeric = data.iloc[:, 1:]

    # Validate numeric data
    if data_numeric.shape[1] < 2:
        raise ValueError("Input data must contain at least two numeric columns.")

    if not all(pd.api.types.is_numeric_dtype(data_numeric[col]) for col in data_numeric.columns):
        raise ValueError("Error: All criteria columns must be numeric.")

    if len(weights) != len(impacts) or len(weights) != data_numeric.shape[1]:
        raise ValueError("Number of weights, impacts, and criteria columns must be equal.")

    for imp in impacts:
        if imp not in ['+', '-']:
            raise ValueError("Impacts must be '+' or '-'.")

    # ---------- TOPSIS IMPLEMENTATION ----------
    matrix = data_numeric.values.astype(float)

    # Normalize
    norm = (matrix ** 2).sum(axis=0) ** 0.5
    normalized = matrix / norm

    # Apply weights
    weighted = normalized * weights

    # Ideal best and worst
    ideal_best = []
    ideal_worst = []

    for j in range(weighted.shape[1]):
        if impacts[j] == '+':
            ideal_best.append(weighted[:, j].max())
            ideal_worst.append(weighted[:, j].min())
        else:
            ideal_best.append(weighted[:, j].min())
            ideal_worst.append(weighted[:, j].max())

    # Separation measures
    s_plus = ((weighted - ideal_best) ** 2).sum(axis=1) ** 0.5
    s_minus = ((weighted - ideal_worst) ** 2).sum(axis=1) ** 0.5

    # Performance...
    score = s_minus / (s_plus + s_minus)

    score_series = pd.Series(score)

    data["Topsis Score"] = score_series
    data["Rank"] = score_series.rank(ascending=False, method="dense").astype(int)
    
    return data

def main():
    if len(sys.argv) < 5:
        print("Usage:")
        print("topsis <input.csv> <weights> <impacts> <output.csv>")
        sys.exit(1)

    filename = sys.argv[1]
    weights_input = sys.argv[2]
    impacts_input = sys.argv[3]
    output_filepath = sys.argv[4]

    try:
        data = pd.read_csv(filename)
        
        try:
            weights = [float(w) for w in weights_input.split(',')]
        except ValueError:
            print("Weights must be numeric and comma-separated.")
            sys.exit(1)

        impacts = impacts_input.split(',')

        result_data = calculate_topsis(data, weights, impacts)

        result_data.to_csv(output_filepath, index=False)
        print("TOPSIS completed successfully")
        print(result_data)

    except FileNotFoundError:
        print("Input file not found.")
        sys.exit(1)

    except Exception as e:
        print("Error:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
