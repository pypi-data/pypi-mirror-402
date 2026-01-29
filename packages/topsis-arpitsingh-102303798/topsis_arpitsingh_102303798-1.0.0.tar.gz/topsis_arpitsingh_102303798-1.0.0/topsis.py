def main():
    import sys
    import pandas as pd
    import numpy as np

    # 1. Check number of arguments
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights_input = sys.argv[2]
    impacts_input = sys.argv[3]
    output_file = sys.argv[4]

    # 2. Read input file
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: Input file not found")
        sys.exit(1)

    # 3. Check minimum columns
    if df.shape[1] < 3:
        print("Error: Input file must contain at least three columns")
        sys.exit(1)

    # 4. Check numeric values (2nd to last columns)
    try:
        data = df.iloc[:, 1:].astype(float)
    except ValueError:
        print("Error: From 2nd to last columns must contain numeric values only")
        sys.exit(1)

    # 5. Process weights & impacts
    weights = weights_input.split(',')
    impacts = impacts_input.split(',')

    n_criteria = data.shape[1]

    if len(weights) != n_criteria or len(impacts) != n_criteria:
        print("Error: Number of weights and impacts must match number of criteria")
        sys.exit(1)

    try:
        weights = np.array(list(map(float, weights)))
    except ValueError:
        print("Error: Weights must be numeric")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be either + or -")
            sys.exit(1)

    # 6. Normalize the decision matrix
    norm_data = data / np.sqrt((data ** 2).sum())

    # 7. Apply weights
    weighted_data = norm_data * weights

    # 8. Ideal best & worst
    ideal_best = np.zeros(n_criteria)
    ideal_worst = np.zeros(n_criteria)

    for i in range(n_criteria):
        if impacts[i] == '+':
            ideal_best[i] = weighted_data.iloc[:, i].max()
            ideal_worst[i] = weighted_data.iloc[:, i].min()
        else:
            ideal_best[i] = weighted_data.iloc[:, i].min()
            ideal_worst[i] = weighted_data.iloc[:, i].max()

    # 9. Distances
    dist_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    # 10. TOPSIS score
    topsis_score = dist_worst / (dist_best + dist_worst)

    # 11. Rank
    df['Topsis Score'] = topsis_score
    df['Rank'] = df['Topsis Score'].rank(ascending=False, method='dense').astype(int)

    # 12. Save output
    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully.")


if __name__ == "__main__":
    main()
