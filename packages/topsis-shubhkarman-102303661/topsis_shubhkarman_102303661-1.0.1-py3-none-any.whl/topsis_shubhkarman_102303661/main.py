import sys
import pandas as pd
import numpy as np

def topsis():
    if len(sys.argv) != 5:
        print("Usage:")
        print("topsis <InputDataFile> <Weights> <Impacts> <OutputResultFile>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    weights = weights_str.split(',')
    impacts = impacts_str.split(',')

    try:
        df = pd.read_csv(input_file)
    except Exception:
        print("Error: Cannot read input file")
        sys.exit(1)

    if len(weights) != df.shape[1] - 1:
        print("Error: Number of weights must match number of columns (excluding first column)")
        sys.exit(1)

    if len(impacts) != df.shape[1] - 1:
        print("Error: Number of impacts must match number of columns (excluding first column)")
        sys.exit(1)

    try:
        weights = np.array(list(map(float, weights)))
    except Exception:
        print("Error: Weights must be numeric")
        sys.exit(1)

    matrix = df.iloc[:, 1:].values.astype(float)

    # Step 1 — Normalize
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / norm

    # Step 2 — Weighted normalized
    weighted = normalized * weights

    # Step 3 — Ideal best/worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted[:, i].max())
            ideal_worst.append(weighted[:, i].min())
        else:
            ideal_best.append(weighted[:, i].min())
            ideal_worst.append(weighted[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4 — Distances
    d_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5 — Scores
    scores = d_worst / (d_best + d_worst)

    df["Topsis Score"] = scores
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)
    print("Result saved to", output_file)
