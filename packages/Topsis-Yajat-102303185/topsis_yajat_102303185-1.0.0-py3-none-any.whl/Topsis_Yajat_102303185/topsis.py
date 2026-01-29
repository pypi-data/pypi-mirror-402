import sys
import pandas as pd
import numpy as np

def topsis(input_file, weights_str, impacts_str, output_file):
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    if df.shape[1] < 3:
        print("Error: Input file must contain three or more columns.")
        sys.exit(1)

    for col in df.columns[1:]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"Error: Column '{col}' contains non-numeric values.")
            sys.exit(1)

    num_criteria = df.shape[1] - 1

    try:
        weights = np.array([float(w) for w in weights_str.split(',')])
    except:
        print("Error: Weights must be numeric values separated by commas.")
        sys.exit(1)

    impacts = impacts_str.split(',')

    if len(weights) != num_criteria:
        print("Error: Number of weights must match number of criteria.")
        sys.exit(1)

    if len(impacts) != num_criteria:
        print("Error: Number of impacts must match number of criteria.")
        sys.exit(1)

    for impact in impacts:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either '+' or '-'.")
            sys.exit(1)

    matrix = df.iloc[:, 1:].values.astype(float)

    norm = np.sqrt(np.sum(matrix**2, axis=0))
    normalized = matrix / norm

    weighted = normalized * weights

    ideal_best = []
    ideal_worst = []

    for j in range(len(impacts)):
        if impacts[j] == '+':
            ideal_best.append(max(weighted[:, j]))
            ideal_worst.append(min(weighted[:, j]))
        else:
            ideal_best.append(min(weighted[:, j]))
            ideal_worst.append(max(weighted[:, j]))

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    s_plus = np.sqrt(np.sum((weighted - ideal_best)**2, axis=1))
    s_minus = np.sqrt(np.sum((weighted - ideal_worst)**2, axis=1))

    scores = s_minus / (s_plus + s_minus)

    ranks = scores.argsort()[::-1].argsort() + 1

    df['Topsis Score'] = np.round(scores, 2)
    df['Rank'] = ranks

    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis <InputDataFile> <Weights> <Impacts> <ResultFileName>")
        print("Example: topsis data.csv \"1,1,1,2,1\" \"+,+,-,+,-\" output.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    topsis(input_file, weights_str, impacts_str, output_file)

if __name__ == "__main__":
    main()
