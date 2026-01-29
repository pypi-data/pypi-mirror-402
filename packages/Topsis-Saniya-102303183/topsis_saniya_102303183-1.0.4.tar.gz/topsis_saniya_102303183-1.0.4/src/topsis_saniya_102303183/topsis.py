import sys
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):

    try:
        data = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: Input file not found")
        sys.exit(1)

    if data.shape[1] < 3:
        print("Error: File must contain at least 3 columns")
        sys.exit(1)

    matrix = data.iloc[:, 1:]

    if not np.all(matrix.applymap(np.isreal)):
        print("Error: Criteria columns must contain only numeric values")
        sys.exit(1)

    weights = weights.split(",")
    impacts = impacts.split(",")

    if len(weights) != matrix.shape[1] or len(impacts) != matrix.shape[1]:
        print("Error: Weights and impacts count mismatch")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be + or -")
            sys.exit(1)

    weights = np.array(weights, dtype=float)
    matrix = matrix.astype(float)

    # Normalization (image formula)
    norm = np.sqrt((matrix ** 2).sum())
    normalized = matrix / norm

    # Weighting
    weighted = normalized * weights

    # Ideal best & worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Distance
    s_plus = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    s_minus = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Topsis Score (image formula)
    score = s_minus / (s_plus + s_minus)

    # Rank
    data["Topsis Score"] = score
    data["Rank"] = score.rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)
    print("TOPSIS completed successfully")

def main():
    if len(sys.argv) != 5:
        print("Usage:")
        print("topsis <InputFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)

    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

if __name__ == "__main__":
    main()
