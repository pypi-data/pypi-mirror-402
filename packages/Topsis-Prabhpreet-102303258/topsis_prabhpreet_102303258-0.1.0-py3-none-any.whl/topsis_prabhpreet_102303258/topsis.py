import sys
import os
import pandas as pd
import numpy as np

def error(msg):
    print("Error:", msg)
    sys.exit(1)

def main():
    # -----------------------------
    # 1. Check number of arguments
    # -----------------------------
    if len(sys.argv) != 5:
        error("Incorrect number of parameters.\nUsage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    # -----------------------------
    # 2. File existence check
    # -----------------------------
    if not os.path.exists(input_file):
        error("Input file not found.")

    # -----------------------------
    # 3. Load file
    # -----------------------------
    try:
        df = pd.read_csv(input_file)
    except Exception:
        error("Unable to read the input file.")

    # -----------------------------
    # 4. Minimum 3 columns check
    # -----------------------------
    if df.shape[1] < 3:
        error("Input file must contain at least three columns.")

    # -----------------------------
    # 5. Extract criteria matrix
    # -----------------------------
    data = df.iloc[:, 1:].copy()

    # -----------------------------
    # 6. Numeric check
    # -----------------------------
    for col in data.columns:
        if not pd.api.types.is_numeric_dtype(data[col]):
            error("From 2nd to last columns must contain numeric values only.")

    # -----------------------------
    # 7. Parse weights & impacts
    # -----------------------------
    try:
        weights = list(map(float, weights_str.split(",")))
    except:
        error("Weights must be numeric and separated by commas.")

    impacts = impacts_str.split(",")

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        error("Number of weights, impacts, and criteria columns must be the same.")

    for imp in impacts:
        if imp not in ["+", "-"]:
            error("Impacts must be either '+' or '-' only.")

    # -----------------------------
    # 8. TOPSIS Computation
    # -----------------------------

    # Step 1: Normalize
    norm = np.sqrt((data**2).sum())
    normalized = data / norm

    # Step 2: Weighting
    weighted = normalized * weights

    # Step 3: Ideal best and worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == "+":
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4: Distance measures
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5: Topsis score
    topsis_score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = topsis_score
    df["Rank"] = df["Topsis Score"].rank(ascending=False, method="dense").astype(int)

    # -----------------------------
    # 9. Save result
    # -----------------------------
    try:
        df.to_csv(output_file, index=False)
        print("TOPSIS analysis completed successfully.")
        print("Result saved to:", output_file)
    except:
        error("Unable to write output file.")

# -----------------------------
# Program Entry
# -----------------------------
if __name__ == "__main__":
    main()
