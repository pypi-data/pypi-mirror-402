import sys
import pandas as pd
import numpy as np


def error(msg):
    print("Error:", msg)
    sys.exit(1)


def topsis(input_file, weights, impacts, output_file):
    try:
        data = pd.read_csv(input_file)
    except:
        error("Input file not found")

    if data.shape[1] < 3:
        error("Input file must contain at least 3 columns")

    criteria = data.iloc[:, 1:]

    if not np.all(criteria.applymap(np.isreal)):
        error("All criteria columns must be numeric")

    weights = list(map(float, weights.split(',')))
    impacts = impacts.split(',')

    if len(weights) != criteria.shape[1]:
        error("Number of weights must match number of criteria")

    if len(impacts) != criteria.shape[1]:
        error("Number of impacts must match number of criteria")

    if not all(i in ['+', '-'] for i in impacts):
        error("Impacts must be + or -")

    # Step 1: Normalize
    norm = criteria / np.sqrt((criteria ** 2).sum())

    # Step 2: Apply weights
    weighted = norm * weights

    # Step 3: Ideal best and worst
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

    # Step 4: Distance from ideal best and worst
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5: Topsis score
    score = dist_worst / (dist_best + dist_worst)

    data["Topsis Score"] = score
    data["Rank"] = score.rank(ascending=False, method="dense").astype(int)

    data.to_csv(output_file, index=False)
    print("TOPSIS completed successfully")


def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)


if __name__ == "__main__":
    main()
