import sys
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):
    try:
        data = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: Input file not found")
        sys.exit(1)

    if data.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        sys.exit(1)

    criteria = data.iloc[:, 1:]

    try:
        criteria = criteria.astype(float)
    except:
        print("Error: From 2nd to last columns must contain numeric values only")
        sys.exit(1)

    weights = weights.split(',')
    impacts = impacts.split(',')

    if len(weights) != criteria.shape[1] or len(impacts) != criteria.shape[1]:
        print("Error: Number of weights, impacts and criteria columns must be same")
        sys.exit(1)

    try:
        weights = np.array(weights, dtype=float)
    except:
        print("Error: Weights must be numeric")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be either + or -")
            sys.exit(1)

    # Step 1: Normalization
    norm = criteria / np.sqrt((criteria ** 2).sum())

    # Step 2: Weighted normalization
    weighted = norm * weights

    # Step 3: Ideal best & worst
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

    # Step 4: Distance calculation
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5: TOPSIS score
    score = dist_worst / (dist_best + dist_worst)

    # Step 6: Ranking
    rank = score.rank(ascending=False)

    data['Topsis Score'] = score
    data['Rank'] = rank.astype(int)

    data.to_csv(output_file, index=False)
    print("TOPSIS successfully completed.")
    print("Output saved to:", output_file)


def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == "__main__":
    main()
