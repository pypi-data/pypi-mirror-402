import pandas as pd
import numpy as np
import sys

def topsis(input_file, weights, impacts, output_file):
    data = pd.read_csv(input_file)

    alternatives = data.iloc[:, 0]
    matrix = data.iloc[:, 1:].values.astype(float)

    weights = np.array([float(w) for w in weights.split(",")])
    impacts = impacts.split(",")

    # Step 1: Normalize
    norm = np.sqrt((matrix**2).sum(axis=0))
    matrix = matrix / norm

    # Step 2: Weighting
    matrix = matrix * weights

    # Step 3: Ideal best & worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == "+":
            ideal_best.append(matrix[:, i].max())
            ideal_worst.append(matrix[:, i].min())
        else:
            ideal_best.append(matrix[:, i].min())
            ideal_worst.append(matrix[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4: Distance
    d_best = np.sqrt(((matrix - ideal_best)**2).sum(axis=1))
    d_worst = np.sqrt(((matrix - ideal_worst)**2).sum(axis=1))

    # Step 5: Score
    score = d_worst / (d_best + d_worst)

    data["Topsis Score"] = score
    data["Rank"] = data["Topsis Score"].rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)
