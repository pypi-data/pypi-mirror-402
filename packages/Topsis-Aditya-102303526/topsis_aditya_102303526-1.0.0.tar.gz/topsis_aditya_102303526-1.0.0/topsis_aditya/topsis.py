import sys
import pandas as pd
import numpy as np

def error(msg):
    print(f"Error: {msg}")
    sys.exit(1)

def topsis():
    if len(sys.argv) != 5:
        error("Usage: topsis <InputFile> <Weights> <Impacts> <OutputFile>")

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    try:
        data = pd.read_excel(input_file)
    except FileNotFoundError:
        error("Input file not found")

    if data.shape[1] < 3:
        error("Input file must contain at least 3 columns")

    criteria = data.iloc[:, 1:]

    if not np.all(criteria.applymap(np.isreal)):
        error("All criteria values must be numeric")

    weights = weights.split(',')
    impacts = impacts.split(',')

    if len(weights) != criteria.shape[1] or len(impacts) != criteria.shape[1]:
        error("Number of weights and impacts must equal number of criteria")

    try:
        weights = np.array(weights, dtype=float)
    except:
        error("Weights must be numeric")

    for i in impacts:
        if i not in ['+', '-']:
            error("Impacts must be either + or -")

    norm = np.sqrt((criteria ** 2).sum())
    normalized = criteria / norm
    weighted = normalized * weights

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
    rank = score.rank(ascending=False)

    data['Topsis Score'] = score
    data['Rank'] = rank.astype(int)

    data.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully.")
