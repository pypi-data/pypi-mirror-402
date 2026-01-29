import sys
import os
import pandas as pd
import numpy as np

def read_input_file(file_path):
    if not os.path.exists(file_path):
        print("Error: Input file not found.")
        sys.exit(1)

    if file_path.endswith(".csv"):
        return pd.read_csv(file_path)
    elif file_path.endswith((".xlsx", ".xls")):
        return pd.read_excel(file_path)
    else:
        print("Error: Unsupported file format.")
        sys.exit(1)

def topsis(input_file, weights, impacts, output_file):
    df = read_input_file(input_file)

    if df.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns.")
        sys.exit(1)

    decision_matrix = df.iloc[:, 1:]

    if not decision_matrix.apply(pd.to_numeric, errors='coerce').notnull().all().all():
        print("Error: Criteria columns must be numeric.")
        sys.exit(1)

    weights = list(map(float, weights.split(",")))
    impacts = impacts.split(",")

    if len(weights) != decision_matrix.shape[1]:
        print("Error: Weights count mismatch.")
        sys.exit(1)

    if len(impacts) != decision_matrix.shape[1]:
        print("Error: Impacts count mismatch.")
        sys.exit(1)

    if any(i not in ['+', '-'] for i in impacts):
        print("Error: Impacts must be '+' or '-'.")
        sys.exit(1)

    norm = decision_matrix / np.sqrt((decision_matrix ** 2).sum())
    weighted = norm * weights

    ideal_best, ideal_worst = [], []

    for i, imp in enumerate(impacts):
        if imp == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)
    rank = score.rank(ascending=False, method='dense')

    result = df.copy()
    result["Topsis Score"] = score
    result["Rank"] = rank.astype(int)

    result.to_csv(output_file, index=False)
    print("TOPSIS completed successfully.")

def main():
    if len(sys.argv) != 5:
        print("Usage:")
        print("topsis <InputFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)

    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

if __name__ == "__main__":
    main()
