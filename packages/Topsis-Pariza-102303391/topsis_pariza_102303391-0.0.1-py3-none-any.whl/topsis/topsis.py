import sys
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):
    try:
        data = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: Input file not found.")
        sys.exit(1)

    if data.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns.")
        sys.exit(1)

    criteria_data = data.iloc[:, 1:]

    if not np.all(criteria_data.applymap(np.isreal)):
        print("Error: Criteria columns must be numeric.")
        sys.exit(1)

    weights = weights.split(',')
    impacts = impacts.split(',')

    if len(weights) != criteria_data.shape[1] or len(impacts) != criteria_data.shape[1]:
        print("Error: Weights and impacts length mismatch.")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be '+' or '-'.")
            sys.exit(1)

    weights = np.array(weights, dtype=float)

    norm = criteria_data / np.sqrt((criteria_data ** 2).sum())
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

    data['TOPSIS Score'] = score
    data['Rank'] = data['TOPSIS Score'].rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully.")

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <inputFile> <weights> <impacts> <outputFile>")
        sys.exit(1)

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)
