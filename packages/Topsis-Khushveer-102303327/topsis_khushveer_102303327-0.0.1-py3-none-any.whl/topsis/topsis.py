import sys
import pandas as pd
import numpy as np
import os


def main():

    # ARGUMENT CHECK 
    if len(sys.argv) != 5:
        print("Error: Incorrect number of arguments")
        sys.exit(1)

    input_file = sys.argv[1]
    weights_input = sys.argv[2]
    impacts_input = sys.argv[3]
    output_file = sys.argv[4]

    # FILE CHECK
    if not os.path.isfile(input_file):
        print("Error: Input file not found")
        sys.exit(1)

    # READ CSV 
    try:
        data = pd.read_csv(input_file)
    except:
        print("Error: Unable to read input file")
        sys.exit(1)

    # COLUMN CHECK
    if data.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        sys.exit(1)

    # NUMERIC CHECK
    criteria_data = data.iloc[:, 1:]

    if not np.all(criteria_data.applymap(lambda x: isinstance(x, (int, float)))):
        print("Error: Columns from 2nd to last must contain numeric values only")
        sys.exit(1)

    # WEIGHTS & IMPACTS 
    weights = weights_input.split(',')
    impacts = impacts_input.split(',')

    if len(weights) != criteria_data.shape[1] or len(impacts) != criteria_data.shape[1]:
        print("Error: Number of weights, impacts and criteria columns must be same")
        sys.exit(1)

    try:
        weights = np.array(weights, dtype=float)
    except:
        print("Error: Weights must be numeric")
        sys.exit(1)

    for impact in impacts:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either + or -")
            sys.exit(1)

    # STEP 1: NORMALIZATION 
    norm_matrix = criteria_data / np.sqrt((criteria_data ** 2).sum())

    # STEP 2: WEIGHTED NORMALIZATION
    weighted_matrix = norm_matrix * weights

    # STEP 3: IDEAL BEST & WORST 
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted_matrix.iloc[:, i].max())
            ideal_worst.append(weighted_matrix.iloc[:, i].min())
        else:
            ideal_best.append(weighted_matrix.iloc[:, i].min())
            ideal_worst.append(weighted_matrix.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # STEP 4: EUCLIDEAN DISTANCE
    S_plus = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    S_minus = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    # STEP 5: TOPSIS SCORE 
    topsis_score = S_minus / (S_plus + S_minus)

    # STEP 6: RANKING 
    data['Topsis Score'] = topsis_score
    data['Rank'] = data['Topsis Score'].rank(
        ascending=False, method='dense'
    ).astype(int)

    # SAVE OUTPUT
    data.to_csv(output_file, index=False)

    print("TOPSIS analysis completed successfully.")


if __name__ == "__main__":
    main()


