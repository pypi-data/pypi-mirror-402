import sys
import pandas as pd
import numpy as np

def main():
    # =========================
    # 1. Check arguments
    # =========================
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFile>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    # =========================
    # 2. Read file
    # =========================
    try:
        data = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: File not found!")
        sys.exit(1)

    # =========================
    # 3. Check columns
    # =========================
    if data.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        sys.exit(1)

    # =========================
    # 4. Extract numeric data
    # =========================
    try:
        matrix = data.iloc[:, 1:].astype(float)
    except:
        print("Error: From 2nd to last column must contain numeric values only")
        sys.exit(1)

    # =========================
    # 5. Parse weights & impacts
    # =========================
    weights = weights.split(",")
    impacts = impacts.split(",")

    if len(weights) != matrix.shape[1] or len(impacts) != matrix.shape[1]:
        print("Error: Number of weights, impacts and criteria columns must be same")
        sys.exit(1)

    try:
        weights = np.array(weights, dtype=float)
    except:
        print("Error: Weights must be numeric")
        sys.exit(1)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be either + or -")
            sys.exit(1)

    # =========================
    # 6. Normalize matrix
    # =========================
    norm = matrix / np.sqrt((matrix**2).sum())

    # =========================
    # 7. Weighted normalized matrix
    # =========================
    weighted = norm * weights

    # =========================
    # 8. Ideal best & worst
    # =========================
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

    # =========================
    # 9. Distance calculation
    # =========================
    dist_best = np.sqrt(((weighted - ideal_best)**2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst)**2).sum(axis=1))

    # =========================
    # 10. Topsis score
    # =========================
    score = dist_worst / (dist_best + dist_worst)

    # =========================
    # 11. Ranking
    # =========================
    data["Topsis Score"] = score
    data["Rank"] = data["Topsis Score"].rank(ascending=False, method="dense").astype(int)

    # =========================
    # 12. Save output
    # =========================
    data.to_csv(output_file, index=False)

    print("TOPSIS successfully applied!")
    print("Output saved to:", output_file)


if __name__ == "__main__":
    main()
