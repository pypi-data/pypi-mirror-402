import sys
import pandas as pd
import numpy as np

def main():
    # Step 1: Check number of arguments
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    # Step 2: Read file
    try:
        data = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: File not found")
        sys.exit(1)

    # Step 3: Check minimum 3 columns
    if data.shape[1] < 3:
        print("Error: Input file must contain three or more columns")
        sys.exit(1)

    # Step 4: Convert weights and impacts to list
    weights = weights.split(",")
    impacts = impacts.split(",")

    n_criteria = data.shape[1] - 1   # excluding first column (name column)

    # Step 5: Check length of weights and impacts
    if len(weights) != n_criteria or len(impacts) != n_criteria:
        print("Error: Number of weights, impacts and criteria must be same")
        sys.exit(1)

    # Step 6: Check impacts validity
    for i in impacts:
        if i not in ["+", "-"]:
            print("Error: Impacts must be either + or -")
            sys.exit(1)

    # Step 7: Check numeric values
    try:
        matrix = data.iloc[:, 1:].astype(float).values
    except:
        print("Error: From 2nd to last columns must contain numeric values only")
        sys.exit(1)

    # Convert weights to float
    weights = np.array(weights, dtype=float)

    # Step 8: Normalize the decision matrix
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / norm

    # Step 9: Multiply by weights
    weighted = normalized * weights

    # Step 10: Find ideal best and ideal worst
    ideal_best = []
    ideal_worst = []

    for i in range(n_criteria):
        if impacts[i] == "+":
            ideal_best.append(weighted[:, i].max())
            ideal_worst.append(weighted[:, i].min())
        else:
            ideal_best.append(weighted[:, i].min())
            ideal_worst.append(weighted[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 11: Calculate distances
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 12: Calculate TOPSIS score
    score = dist_worst / (dist_best + dist_worst)

    # Step 13: Add score and rank to data
    data["Topsis Score"] = score
    data["Rank"] = data["Topsis Score"].rank(ascending=False).astype(int)

    # Step 14: Save output
    data.to_csv(output_file, index=False)
    print("Result saved in", output_file)


def run():
    main()

if __name__ == "__main__":
    main()

