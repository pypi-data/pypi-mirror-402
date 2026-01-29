import sys
import pandas as pd
import numpy as np

def main():
    if len(sys.argv) != 4:
        print("Usage: topsis <input_file.csv> <weights> <impacts>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2].split(',')
    impacts = sys.argv[3].split(',')

    weights = np.array(weights, dtype=float)

    data = pd.read_csv(input_file)

    if len(weights) != data.shape[1] - 1:
        print("Error: Number of weights not equal to number of criteria")
        sys.exit(1)

    if len(impacts) != data.shape[1] - 1:
        print("Error: Number of impacts not equal to number of criteria")
        sys.exit(1)

    matrix = data.iloc[:, 1:].values

    # Normalize
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / norm

    # Weight
    weighted = normalized * weights

    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted[:, i].max())
            ideal_worst.append(weighted[:, i].min())
        elif impacts[i] == '-':
            ideal_best.append(weighted[:, i].min())
            ideal_worst.append(weighted[:, i].max())
        else:
            print("Error: Impacts must be + or -")
            sys.exit(1)

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    data['Topsis Score'] = score
    data['Rank'] = data['Topsis Score'].rank(ascending=False)

    data.to_csv("output.csv", index=False)
    print("Result saved in output.csv")

if __name__ == "__main__":
    main()
