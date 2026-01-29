import numpy as np
import pandas as pd
import sys

def topsis(input_file, weights, impacts, output_file):
    data = pd.read_csv(input_file)

    if data.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        sys.exit(1)
    
    alternatives = data.iloc[:, 0]
    matrix = data.iloc[:, 1:]

    if not np.all(np.isfinite(matrix.to_numpy())):
        print("Error: All criteria values must be numeric")
        sys.exit(1)
    
    weights = weights.split(",")
    impacts = impacts.split(",")

    if len(weights) != matrix.shape[1] or len(impacts) != matrix.shape[1]:
        print("Error: Number of weights and impacts must match number of criteria")
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

    weights = weights / np.sum(weights)     
    norm_matrix = matrix / np.sqrt((matrix ** 2).sum())
    weighted_matrix = norm_matrix * weights
    
    ideal_best = []
    ideal_worst = []
    
    for i in range(len(impacts)):
        column = weighted_matrix.iloc[:, i]
        if impacts[i] == '+':
            ideal_best.append(column.max())
            ideal_worst.append(column.min())
        else:
            ideal_best.append(column.min())
            ideal_worst.append(column.max())

    dist_best = np.sqrt(((weighted_matrix - ideal_best)**2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst)**2).sum(axis=1))
    
    scores = dist_worst / (dist_best + dist_worst)
    
    ranks = scores.rank(ascending=False)

    data["Topsis Score"] = scores
    data["Rank"] = ranks.astype(int)

    data.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully")


def main():
    import sys
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <ResultFileName>")
        sys.exit(1)

    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == "__main__":
    main()
