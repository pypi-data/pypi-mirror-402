import sys
import os
import numpy as np
import pandas as pd

def error(msg):
    print(f"Error: {msg}")
    sys.exit(1)


def parse_list(arg, kind):
    """
    Parses comma-separated weights or impacts
    """
    items = arg.split(",")

    if len(items) == 0:
        error(f"{kind} cannot be empty")

    return items

def validate_input_file(input_file, weights, impacts):
    try:
        df = pd.read_csv(input_file)
    except Exception:
        error("Unable to read input file. Ensure it is a valid CSV.")

    # Must have at least 3 columns
    if df.shape[1] < 3:
        error("Input file must contain at least three columns.")

    # Extract criteria columns (2nd to last)
    criteria = df.iloc[:, 1:]

    # Check numeric-only criteria
    if not criteria.apply(pd.to_numeric, errors="coerce").notnull().all().all():
        error("From 2nd to last columns must contain numeric values only.")

    # Check criteria count matches weights & impacts
    if criteria.shape[1] != len(weights):
        error(
            "Number of weights, impacts, and criteria columns must be the same."
        )

    return df

def compute_topsis(df, weights, impacts):
    # Extract criteria matrix (2nd to last columns)
    criteria = df.iloc[:, 1:].values.astype(float)

    # Step 1: Normalize
    norm = np.sqrt((criteria ** 2).sum(axis=0))
    normalized = criteria / norm

    # Step 2: Normalize weights to sum to 1
    weights = np.array(weights, dtype=float)

    weight_sum = weights.sum()
    if weight_sum == 0:
        error("Sum of weights must be greater than 0")

    weights = weights / weight_sum

    # Apply weights
    weighted = normalized * weights

    # Step 3: Ideal best and worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == "+":
            ideal_best.append(weighted[:, i].max())
            ideal_worst.append(weighted[:, i].min())
        else:
            ideal_best.append(weighted[:, i].min())
            ideal_worst.append(weighted[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4: Distance calculation
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5: Topsis score
    score = dist_worst / (dist_best + dist_worst)

    return score

def main():
    # Expected arguments:
    # cli.py input.csv weights impacts output.csv
    if len(sys.argv) != 5:
        error(
            "Incorrect number of arguments.\n"
            "Usage: python cli.py <input.csv> <weights> <impacts> <output.csv>"
        )

    input_file = sys.argv[1]
    weights_arg = sys.argv[2]
    impacts_arg = sys.argv[3]
    output_file = sys.argv[4]

    # Check input file exists
    if not os.path.isfile(input_file):
        error(f"Input file '{input_file}' not found")

    # Parse weights and impacts
    weights = parse_list(weights_arg, "Weights")
    impacts = parse_list(impacts_arg, "Impacts")

    # Check same length
    if len(weights) != len(impacts):
        error("Number of weights must be equal to number of impacts")

    # Validate weights are numeric
    try:
        weights = [float(w) for w in weights]
    except ValueError:
        error("Weights must be numeric values separated by commas")

    # Validate impacts
    for i in impacts:
        if i not in ["+", "-"]:
            error("Impacts must be either '+' or '-'")

    df = validate_input_file(input_file, weights, impacts)

    scores = compute_topsis(df, weights, impacts)

    df["Topsis Score"] = scores
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)

    print("TOPSIS computation completed successfully.")
    print("Output written to:", output_file)


def run():
    main()