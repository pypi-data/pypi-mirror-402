import sys
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):
    try:
        # load the dataset
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: File not found")
        sys.exit(1)

    # basic validation
    if df.shape[1] < 3:
        print("Error: File must have at least 3 cols")
        sys.exit(1)

    # try converting numeric part to float to catch errors
    try:
        temp_df = df.iloc[:, 1:].astype(float)
    except ValueError:
        print("Error: Columns from 2nd onwards must be numeric")
        sys.exit(1)

    # process weights and impacts
    w = [float(x) for x in weights.split(',')]
    imp = impacts.split(',')

    if len(w) != temp_df.shape[1] or len(imp) != temp_df.shape[1]:
        print("Error: Weights/Impacts length mismatch")
        sys.exit(1)

    if not all(x in ['+', '-'] for x in imp):
        print("Error: Impacts must be + or -")
        sys.exit(1)

    # ----------------------------
    # Step 1: Normalization
    # ----------------------------
    # calc root sum of squares for each col
    rss = np.sqrt((temp_df**2).sum())
    
    # divide to get normalized matrix
    df_norm = temp_df.div(rss)

    # ----------------------------
    # Step 2: Weight Assignment
    # ----------------------------
    # multiply each col by its weight
    df_weighted = df_norm * w

    # ----------------------------
    # Step 3: Find Ideal Best/Worst
    # ----------------------------
    ideal_best = []
    ideal_worst = []

    for i, impact in enumerate(imp):
        col = df_weighted.iloc[:, i]
        if impact == '+':
            ideal_best.append(col.max())
            ideal_worst.append(col.min())
        else:
            # for negative impact, min is best
            ideal_best.append(col.min())
            ideal_worst.append(col.max())

    # ----------------------------
    # Step 4: Euclidean Distances
    # ----------------------------
    # distance from best (S+) and worst (S-)
    S_plus = np.sqrt(((df_weighted - ideal_best) ** 2).sum(axis=1))
    S_minus = np.sqrt(((df_weighted - ideal_worst) ** 2).sum(axis=1))

    # ----------------------------
    # Step 5: Performance Score
    # ----------------------------
    # calc similarity score
    p_score = S_minus / (S_plus + S_minus)

    # append results to original df
    df['Topsis Score'] = p_score
    
    # rank based on score (higher is better)
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    # save final file
    df.to_csv(output_file, index=False)
    print("File saved successfully")

# logic to run the function
if __name__ == "__main__":
    topsis(
        "102303670-data.csv",
        "1,1,1,1,2",
        "+,+,-,+,+",
        "102303670-result.csv"
    )