import sys
import pandas as pd
import numpy as np

def main():

    if len(sys.argv) != 5:
        print("Usage:")
        print("python topsis.py <input.xlsx> <weights> <impacts> <output.xlsx>")
        return

    input_file = sys.argv[1]
    weights = sys.argv[2].split(",")
    impacts = sys.argv[3].split(",")
    output_file = sys.argv[4]


    try:
        df = pd.read_excel(input_file)
    except:
        print("Error: File not found")
        return


    if df.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        return

    criteria = df.iloc[:, 1:]

    if not np.all(criteria.applymap(np.isreal)):
        print("Error: Non-numeric values found")
        return

    if len(weights) != criteria.shape[1]:
        print("Error: Number of weights must match number of criteria")
        return

    if len(impacts) != criteria.shape[1]:
        print("Error: Number of impacts must match number of criteria")
        return

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be either + or -")
            return

    weights = np.array(weights, dtype=float)



    normalized = criteria / np.sqrt((criteria ** 2).sum())
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

    distance_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    topsis_score = distance_worst / (distance_best + distance_worst)

    df["Topsis Score"] = topsis_score
    df["Rank"] = topsis_score.rank(ascending=False).astype(int)


    df.to_excel(output_file, index=False)
    print(" Output file generated successfully:", output_file)


if __name__ == "__main__":
    main()

def run():
    main()
