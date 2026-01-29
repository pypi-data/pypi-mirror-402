import sys
import os
import pandas as pd
import numpy as np


def error(msg):
    print(f"Error: {msg}")
    sys.exit(1)


def main():
    # -----------------------------
    # 1. Check number of arguments
    # -----------------------------
    if len(sys.argv) != 5:
        error(
            "Incorrect number of parameters.\n"
            "Usage:\n"
            "python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>"
        )

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    # -----------------------------
    # 2. File not found handling
    # -----------------------------
    if not os.path.isfile(input_file):
        error("Input file not found.")

    # -----------------------------
    # 3. Read CSV
    # -----------------------------
    try:
        data = pd.read_csv(input_file)
    except Exception:
        error("Unable to read input file. Ensure it is a valid CSV.")

    # -----------------------------
    # 4. Minimum 3 columns check
    # -----------------------------
    if data.shape[1] < 3:
        error("Input file must contain three or more columns.")

    # -----------------------------
    # 5. Extract criteria columns
    # -----------------------------
    criteria_data = data.iloc[:, 1:]

    # -----------------------------
    # 6. Check numeric values
    # -----------------------------
    if not all(criteria_data.dtypes.apply(lambda x: np.issubdtype(x, np.number))):
        error("From 2nd to last columns must contain numeric values only.")

    # -----------------------------
    # 7. Parse weights & impacts
    # -----------------------------
    try:
        weights = list(map(float, weights_str.split(",")))
    except ValueError:
        error("Weights must be numeric and separated by commas.")

    impacts = impacts_str.split(",")

    # -----------------------------
    # 8. Count consistency check
    # -----------------------------
    if len(weights) != criteria_data.shape[1]:
        error("Number of weights must be equal to number of criteria.")

    if len(impacts) != criteria_data.shape[1]:
        error("Number of impacts must be equal to number of criteria.")

    # -----------------------------
    # 9. Validate impacts
    # -----------------------------
    for impact in impacts:
        if impact not in ["+", "-"]:
            error("Impacts must be either '+' or '-'.")

    # -----------------------------
    # 10. Normalize matrix
    # -----------------------------
    norm_matrix = criteria_data / np.sqrt((criteria_data ** 2).sum())

    # -----------------------------
    # 11. Apply weights
    # -----------------------------
    weighted_matrix = norm_matrix * weights

    # -----------------------------
    # 12. Ideal best & worst
    # -----------------------------
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == "+":
            ideal_best.append(weighted_matrix.iloc[:, i].max())
            ideal_worst.append(weighted_matrix.iloc[:, i].min())
        else:
            ideal_best.append(weighted_matrix.iloc[:, i].min())
            ideal_worst.append(weighted_matrix.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # -----------------------------
    # 13. Distance calculation
    # -----------------------------
    dist_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    # -----------------------------
    # 14. TOPSIS score
    # -----------------------------
    score = dist_worst / (dist_best + dist_worst)

    # -----------------------------
    # 15. Rank calculation
    # -----------------------------
    rank = score.rank(ascending=False, method="dense").astype(int)

    # -----------------------------
    # 16. Output result
    # -----------------------------
    result = data.copy()
    result["Distance from Ideal Best"] = dist_best
    result["Distance from Ideal Worst"] = dist_worst
    result["TOPSIS Score"] = score
    result["Rank"] = rank

    result.to_csv(output_file, index=False)

    print("TOPSIS analysis completed successfully.")
    print(f"Result saved to '{output_file}'.")


if __name__ == "__main__":
    main()
