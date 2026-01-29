import sys
import os
import numpy as np
import pandas as pd

# -------------------- Error Handling --------------------

def exit_error(msg):
    print(f"Error: {msg}")
    sys.exit(1)

# -------------------- Argument Validation --------------------

def validate_arguments():
    if len(sys.argv) != 5:
        exit_error(
            "Incorrect number of parameters.\n"
            "Usage:\n"
            "python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFile>"
        )

# -------------------- Read & Validate CSV --------------------

def read_csv_file(filename):
    if not os.path.exists(filename):
        exit_error("Input file not found.")

    try:
        df = pd.read_csv(filename)
    except Exception:
        exit_error("Unable to read input file.")

    if df.shape[1] < 3:
        exit_error("Input file must contain at least 3 columns.")

    return df

def validate_numeric_data(df):
    data = df.iloc[:, 1:]

    for col in data.columns:
        if not pd.api.types.is_numeric_dtype(data[col]):
            exit_error(
                "From 2nd to last columns must contain numeric values only."
            )

    return data.astype(float)

# -------------------- Weights & Impacts --------------------

def parse_weights_impacts(weights_str, impacts_str, num_criteria):
    weights = weights_str.split(",")
    impacts = impacts_str.split(",")

    if len(weights) != num_criteria or len(impacts) != num_criteria:
        exit_error(
            "Number of weights, impacts, and criteria columns must be the same."
        )

    try:
        weights = np.array(list(map(float, weights)))
    except ValueError:
        exit_error("Weights must be numeric values separated by commas.")

    for imp in impacts:
        if imp not in ["+", "-"]:
            exit_error("Impacts must be either '+' or '-' only.")

    return weights, impacts

# -------------------- TOPSIS (MCDM) FUNCTIONS --------------------

def normalize_matrix(matrix):
    denominator = np.sqrt((matrix ** 2).sum(axis=0))
    return matrix / denominator

def weighted_normalized_matrix(norm_matrix, weights):
    return norm_matrix * weights

def ideal_solutions(weighted_matrix, impacts):
    best, worst = [], []

    for j in range(weighted_matrix.shape[1]):
        if impacts[j] == "+":
            best.append(weighted_matrix[:, j].max())
            worst.append(weighted_matrix[:, j].min())
        else:
            best.append(weighted_matrix[:, j].min())
            worst.append(weighted_matrix[:, j].max())

    return np.array(best), np.array(worst)

def separation_measures(weighted_matrix, ideal_best, ideal_worst):
    s_plus = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    s_minus = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))
    return s_plus, s_minus

def topsis_score(s_plus, s_minus):
    return s_minus / (s_plus + s_minus)

def rank_results(scores):
    return scores.rank(ascending=False, method="dense")

# -------------------- MAIN --------------------

def main():
    validate_arguments()

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    df = read_csv_file(input_file)
    decision_matrix = validate_numeric_data(df)

    num_criteria = decision_matrix.shape[1]

    weights, impacts = parse_weights_impacts(
        weights_str, impacts_str, num_criteria
    )

    norm_matrix = normalize_matrix(decision_matrix.values)
    weighted_matrix = weighted_normalized_matrix(norm_matrix, weights)

    ideal_best, ideal_worst = ideal_solutions(weighted_matrix, impacts)
    s_plus, s_minus = separation_measures(
        weighted_matrix, ideal_best, ideal_worst
    )

    scores = topsis_score(s_plus, s_minus)

    df["Topsis Score"] = scores
    df["Rank"] = rank_results(df["Topsis Score"])

    try:
        df.to_csv(output_file, index=False)
    except Exception:
        exit_error("Unable to write output file.")

    print("TOPSIS analysis completed successfully.")
    print(f"Output saved to: {output_file}")

# -------------------- ENTRY POINT --------------------

if __name__ == "__main__":
    main()
