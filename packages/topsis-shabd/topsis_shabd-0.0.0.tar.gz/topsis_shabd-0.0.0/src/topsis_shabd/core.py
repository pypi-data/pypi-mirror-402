import sys
import os
import pandas as pd
import numpy as np

def error_exit(msg):
    print(f"Error: {msg}")
    sys.exit(1)

def topsis(input_file, weights, impacts, output_file):
    if not os.path.exists(input_file):
        error_exit("Input file not found")

    try:
        data = pd.read_excel(input_file)
    except:
        error_exit("Unable to read input file")

    if data.shape[1] < 3:
        error_exit("Input file must contain three or more columns")

    criteria_data = data.iloc[:, 1:]

    # Check if all values in criteria columns are numeric
    for col in criteria_data.columns:
        if not pd.api.types.is_numeric_dtype(criteria_data[col]):
            error_exit("From 2nd to last columns must contain numeric values only")

    # Split and strip whitespace
    weights = [w.strip() for w in weights.split(",")]
    impacts = [i.strip() for i in impacts.split(",")]

    # Check if weights and impacts are not empty after splitting
    if len(weights) == 0 or weights[0] == '':
        error_exit("Weights must be separated by commas")
    if len(impacts) == 0 or impacts[0] == '':
        error_exit("Impacts must be separated by commas")

    if len(weights) != criteria_data.shape[1]:
        error_exit("Number of weights must match number of criteria")

    if len(impacts) != criteria_data.shape[1]:
        error_exit("Number of impacts must match number of criteria")

    try:
        weights = np.array(weights, dtype=float)
    except:
        error_exit("Weights must be numeric")

    for impact in impacts:
        if impact not in ["+", "-"]:
            error_exit("Impacts must be either + or -")

    norm_data = criteria_data / np.sqrt((criteria_data ** 2).sum())
    weighted_data = norm_data * weights

    ideal_best = []
    ideal_worst = []

    for i in range(weighted_data.shape[1]):
        if impacts[i] == "+":
            ideal_best.append(weighted_data.iloc[:, i].max())
            ideal_worst.append(weighted_data.iloc[:, i].min())
        else:
            ideal_best.append(weighted_data.iloc[:, i].min())
            ideal_worst.append(weighted_data.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    topsis_score = dist_worst / (dist_best + dist_worst)

    data["Topsis Score"] = topsis_score
    data["Rank"] = data["Topsis Score"].rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)
    print(f"TOPSIS Result saved to {output_file}")



