import sys
import pandas as pd
import numpy as np

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = list(map(float, sys.argv[2].split(',')))
    impacts = sys.argv[3].split(',')
    output_file = sys.argv[4]

    data = pd.read_csv(input_file)

    if data.shape[1] < 3:
        print("Error: Input file must contain three or more columns.")
        sys.exit(1)

    names = data.iloc[:, 0]
    matrix = data.iloc[:, 1:].values

    if len(weights) != matrix.shape[1] or len(impacts) != matrix.shape[1]:
        print("Error: Number of weights, impacts, and columns must be same.")
        sys.exit(1)

    # Normalize
    norm = np.sqrt((matrix**2).sum(axis=0))
    matrix = matrix / norm

    # Weighting
    matrix = matrix * weights

    # Ideal best and worst
    ideal_best = []
    ideal_worst = []

    for i in range(matrix.shape[1]):
        if impacts[i] == '+':
            ideal_best.append(matrix[:, i].max())
            ideal_worst.append(matrix[:, i].min())
        else:
            ideal_best.append(matrix[:, i].min())
            ideal_worst.append(matrix[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Distances
    dist_best = np.sqrt(((matrix - ideal_best)**2).sum(axis=1))
    dist_worst = np.sqrt(((matrix - ideal_worst)**2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    data['Topsis Score'] = score
    data['Rank'] = score.rank(ascendi
