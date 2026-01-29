import sys
import pandas as pd
import numpy as np

def error(msg):
    print(f"Error: {msg}")
    sys.exit(1)

def topsis(input_file, weights, impacts, output_file):
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        error("Input file not found")

    if df.shape[1] < 3:
        error("Input file must contain three or more columns")

    data = df.iloc[:, 1:]

    # Check numeric values
    if not np.all(data.applymap(np.isreal)):
        error("From 2nd to last columns must contain numeric values only")

    try:
        weights = list(map(float, weights.split(",")))
    except:
        error("Weights must be numeric and separated by commas")

    impacts = impacts.split(",")

    if len(weights) != data.shape[1]:
        error("Number of weights must match number of criteria")

    if len(impacts) != data.shape[1]:
        error("Number of impacts must match number of criteria")

    for i in impacts:
        if i not in ['+', '-']:
            error("Impacts must be either + or -")

    # Step 1: Normalize
    norm_data = data / np.sqrt((data ** 2).sum())

    # Step 2: Weighting
    weighted_data = norm_data * weights

    # Step 3: Ideal best & worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted_data.iloc[:, i].max())
            ideal_worst.append(weighted_data.iloc[:, i].min())
        else:
            ideal_best.append(weighted_data.iloc[:, i].min())
            ideal_worst.append(weighted_data.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4: Distance calculation
    dist_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    # Step 5: Topsis Score
    topsis_score = dist_worst / (dist_best + dist_worst)

    # Step 6: Ranking
    df['Topsis Score'] = topsis_score
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        error("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFileName>")

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)



def main():
    import sys

    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    topsis(input_file, weights, impacts, output_file)


if __name__ == "__main__":
    main()