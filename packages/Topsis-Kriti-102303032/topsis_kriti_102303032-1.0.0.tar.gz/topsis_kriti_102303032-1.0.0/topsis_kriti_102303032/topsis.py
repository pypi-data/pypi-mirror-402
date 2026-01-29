import sys
import pandas as pd
import numpy as np

def topsis():
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <input.csv> <weights> <impacts> <output.csv>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = list(map(float, sys.argv[2].split(',')))
    impacts = sys.argv[3].split(',')
    output_file = sys.argv[4]

    data = pd.read_csv(input_file)

    if len(weights) != data.shape[1] - 1:
        raise ValueError("Number of weights must match number of criteria")

    if len(impacts) != data.shape[1] - 1:
        raise ValueError("Number of impacts must match number of criteria")

    matrix = data.iloc[:, 1:].values.astype(float)

    # Step 1: Normalize
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    norm_matrix = matrix / norm

    # Step 2: Apply weights
    weighted_matrix = norm_matrix * weights

    # Step 3: Ideal best & worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted_matrix[:, i].max())
            ideal_worst.append(weighted_matrix[:, i].min())
        else:
            ideal_best.append(weighted_matrix[:, i].min())
            ideal_worst.append(weighted_matrix[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4: Distance
    dist_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    # Step 5: Score
    score = dist_worst / (dist_best + dist_worst)

    data['Topsis Score'] = score
    data['Rank'] = score.rank(ascending=False)

    data.to_csv(output_file, index=False)
    print("TOPSIS completed successfully")
