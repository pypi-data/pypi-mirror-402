import sys
import pandas as pd
import numpy as np


def topsis(input_file, weights, impacts, output_file):

    try:
        data = pd.read_csv(input_file)
    except FileNotFoundError:
        raise Exception("Input file not found")

    if data.shape[1] < 3:
        raise Exception("Input file must contain three or more columns")

    try:
        matrix = data.iloc[:, 1:].astype(float)
    except ValueError:
        raise Exception("From 2nd to last columns must contain numeric values only")

    weights = weights.split(',')
    impacts = impacts.split(',')

    if len(weights) != matrix.shape[1]:
        raise Exception("Number of weights must match number of criteria")

    if len(impacts) != matrix.shape[1]:
        raise Exception("Number of impacts must match number of criteria")

    for i in impacts:
        if i not in ['+', '-']:
            raise Exception("Impacts must be + or -")

    weights = np.array(weights, dtype=float)

    # Normalization
    norm_matrix = matrix / np.sqrt((matrix ** 2).sum())
    weighted_matrix = norm_matrix * weights

    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted_matrix.iloc[:, i].max())
            ideal_worst.append(weighted_matrix.iloc[:, i].min())
        else:
            ideal_best.append(weighted_matrix.iloc[:, i].min())
            ideal_worst.append(weighted_matrix.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    data['Topsis Score'] = score
    data['Rank'] = data['Topsis Score'].rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)
    print("TOPSIS completed successfully")


def main():
    if len(sys.argv) != 5:
        print("Usage:")
        print("topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        sys.exit(1)

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)


if __name__ == "__main__":
    main()

