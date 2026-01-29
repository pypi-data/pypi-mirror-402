import sys
import os
import pandas as pd
import numpy as np

def main():

    if not os.path.isfile(sys.argv[1]):
        print("Error: Input file not found")
        sys.exit(1)

    data = pd.read_csv(sys.argv[1])

    if data.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        sys.exit(1)

    criteria = data.iloc[:, 1:]

    if not criteria.applymap(lambda x: isinstance(x, (int, float))).all().all():
        print("Error: Criteria columns must be numeric")
        sys.exit(1)

    weights = list(map(float, sys.argv[2].split(",")))
    impacts = sys.argv[3].split(",")

    if len(weights) != criteria.shape[1]:
        print("Error: Number of weights must match number of criteria")
        sys.exit(1)

    if len(impacts) != criteria.shape[1]:
        print("Error: Number of impacts must match number of criteria")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be + or -")
            sys.exit(1)

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

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    scores = dist_worst / (dist_best + dist_worst)

    data["Topsis Score"] = scores
    data["Rank"] = scores.rank(ascending=False).astype(int)

    data.to_csv(sys.argv[4], index=False)
    print("TOPSIS completed successfully")
