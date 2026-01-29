import sys
import os
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):

    #File Check
    if not os.path.exists(input_file):
        print("Error: Input file not found.")
        sys.exit(1)

    try:
        if input_file.endswith('.xlsx'):
            df = pd.read_excel(input_file)
        else:
            df = pd.read_csv(input_file)
    except Exception:
        print("Error: Unable to read the input file.")
        sys.exit(1)

    #Column Check
    if df.shape[1] < 3:
        print("Error: Input file must contain at least three columns.")
        sys.exit(1)

    #Criteria Data
    data = df.iloc[:, 1:]

    #Numeric Check
    if not data.apply(lambda col: np.issubdtype(col.dtype, np.number)).all():
        print("Error: From 2nd to last columns must contain numeric values only.")
        sys.exit(1)

    #Weights & Impacts Processing
    try:
        weights = list(map(float, weights.split(",")))
        impacts = impacts.split(",")
    except Exception:
        print("Error: Weights and impacts must be comma-separated.")
        sys.exit(1)

    if len(weights) != data.shape[1]:
        print("Error: Number of weights must match number of criteria.")
        sys.exit(1)

    if len(impacts) != data.shape[1]:
        print("Error: Number of impacts must match number of criteria.")
        sys.exit(1)

    for impact in impacts:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either '+' or '-'.")
            sys.exit(1)

    #Decision Matrix Normalization
    norm = np.sqrt((data ** 2).sum())
    normalized_data = data / norm

    #Apply Weights
    weighted_data = normalized_data * weights

    #Ideal Best and Worst
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

    #Distance
    distance_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    #TOPSIS Score
    score = distance_worst / (distance_best + distance_worst)

    #Rank
    df['Topsis Score'] = score
    df['Rank'] = score.rank(ascending=False, method='dense')

    
    df.to_csv(output_file, index=False)

    print("TOPSIS analysis completed successfully.")
    print(f"Result saved to '{output_file}'")


def main():
    import sys
    if len(sys.argv) != 5:
        print("Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        sys.exit(1)

    topsis(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4]
    )

if __name__ == "__main__":
    main()
