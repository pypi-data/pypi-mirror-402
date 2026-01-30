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
        error("Input file must have at least 3 columns")

    criteria = data.iloc[:, 1:]

    if not np.all(criteria.applymap(np.isreal)):
        error("Criteria values must be numeric")

    weights = list(map(float, weights.split(',')))
    impacts = impacts.split(',')

    if len(weights) != criteria.shape[1]:
        error("Weights count mismatch")

    if len(impacts) != criteria.shape[1]:
        error("Impacts count mismatch")

    if not all(i in ['+', '-'] for i in impacts):
        error("Impacts must be + or -")

    norm = criteria / np.sqrt((criteria ** 2).sum())
    weighted = norm * weights

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

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    data["Topsis Score"] = score
    data["Rank"] = score.rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)
    print("TOPSIS completed successfully")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        error("Usage: python topsis.py <input> <weights> <impacts> <output>")

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)
