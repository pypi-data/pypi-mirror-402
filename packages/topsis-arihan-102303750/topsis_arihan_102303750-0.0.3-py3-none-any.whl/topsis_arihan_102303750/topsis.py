import sys
import pandas as pd
import numpy as np

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        return

    input_file = sys.argv[1]
    weights = sys.argv[2].split(',')
    impacts = sys.argv[3].split(',')
    output_file = sys.argv[4]

    try:
        data = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: Input file not found")
        return

    if data.shape[1] < 3:
        print("Error: Input file must contain three or more columns")
        return

    criteria = data.iloc[:, 1:]

    try:
        criteria = criteria.astype(float)
    except:
        print("Error: From 2nd to last columns must contain numeric values only")
        return

    if len(weights) != criteria.shape[1] or len(impacts) != criteria.shape[1]:
        print("Error: Number of weights, impacts and criteria columns must be same")
        return

    weights = np.array(weights, dtype=float)

    for impact in impacts:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either + or -")
            return

    norm = criteria / np.sqrt((criteria ** 2).sum())
    weighted = norm * weights

    ideal_best, ideal_worst = [], []
    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    data["Topsis Score"] = score.round(3)
    data["Rank"] = data["Topsis Score"].rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully")
