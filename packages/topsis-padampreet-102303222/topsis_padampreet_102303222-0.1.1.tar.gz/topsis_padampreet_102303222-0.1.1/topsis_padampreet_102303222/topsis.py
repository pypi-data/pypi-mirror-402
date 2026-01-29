import sys
import os
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):

    if not os.path.isfile(input_file):
        raise FileNotFoundError("Input file not found")

    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        raise Exception("Input file must contain three or more columns")

    data = df.iloc[:, 1:]

    if not np.all(data.applymap(np.isreal)):
        raise Exception("All criteria values must be numeric")

    weights = list(map(float, weights.split(",")))
    impacts = impacts.split(",")

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        raise Exception("Number of weights, impacts, and criteria must be same")

    for i in impacts:
        if i not in ['+', '-']:
            raise Exception("Impacts must be + or -")

    norm = data / np.sqrt((data ** 2).sum())
    weights = np.array(weights) / np.sum(weights)
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

    s_plus = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    s_minus = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = s_minus / (s_plus + s_minus)
    df['Topsis Score'] = score
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

if __name__ == "__main__":
    main()
