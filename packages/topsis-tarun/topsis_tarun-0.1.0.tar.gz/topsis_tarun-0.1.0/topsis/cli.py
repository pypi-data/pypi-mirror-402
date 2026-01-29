import sys
import pandas as pd
import numpy as np

def error(msg):
    print(f"Error: {msg}")
    sys.exit(1)

def main():
    if len(sys.argv) != 5:
        error("Incorrect number of parameters.\nUsage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFileName>")

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        error("Input file not found")

    if df.shape[1] < 3:
        error("Input file must contain three or more columns")

    data = df.iloc[:, 1:]

    if not np.all(data.applymap(np.isreal)):
        error("From 2nd to last columns must contain numeric values only")

    try:
        weights = list(map(float, weights_str.split(',')))
        impacts = impacts_str.split(',')
    except:
        error("Weights and impacts must be comma separated")

    if len(weights) != len(impacts) or len(weights) != data.shape[1]:
        error("Number of weights, impacts, and criteria columns must be the same")

    for i in impacts:
        if i not in ['+', '-']:
            error("Impacts must be either + or -")

    norm = data / np.sqrt((data ** 2).sum())
    weighted = norm * weights

    ideal_best, ideal_worst = [], []

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

    df['Topsis Score'] = score
    df['Rank'] = df['Topsis Score'].rank(ascending=False, method='dense').astype(int)

    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully")

if __name__ == "__main__":
    main()