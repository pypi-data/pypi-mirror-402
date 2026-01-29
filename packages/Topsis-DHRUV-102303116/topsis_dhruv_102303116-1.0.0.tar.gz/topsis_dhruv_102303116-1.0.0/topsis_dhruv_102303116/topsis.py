import sys
import os
import pandas as pd
import numpy as np

def is_number(x):
    try:
        float(x)
        return True
    except:
        return False

def read_file(input_file):
    ext = os.path.splitext(input_file)[1].lower()

    if ext == ".csv":
        return pd.read_csv(input_file)
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(input_file)
    else:
        raise Exception("Input file must be .csv or .xlsx/.xls")

def topsis(data, weights, impacts):
    df = data.copy()

    if df.shape[1] < 3:
        raise Exception("Input file must have at least 3 columns")

    fund_col = df.columns[0]
    criteria_cols = df.columns[1:]

    for col in criteria_cols:
        if not df[col].apply(is_number).all():
            raise Exception(f"Column '{col}' must contain only numeric values")
        df[col] = df[col].astype(float)

    if len(weights) != len(criteria_cols):
        raise Exception("Number of weights must be equal to number of criteria columns")

    if len(impacts) != len(criteria_cols):
        raise Exception("Number of impacts must be equal to number of criteria columns")

    for imp in impacts:
        if imp not in ["+", "-"]:
            raise Exception("Impacts must be either '+' or '-' only")

    matrix = df[criteria_cols].values

    norm = np.sqrt((matrix ** 2).sum(axis=0))
    norm_matrix = matrix / norm

    weights = np.array(weights)
    weighted_matrix = norm_matrix * weights

    ideal_best = np.zeros(len(criteria_cols))
    ideal_worst = np.zeros(len(criteria_cols))

    for j in range(len(criteria_cols)):
        if impacts[j] == "+":
            ideal_best[j] = np.max(weighted_matrix[:, j])
            ideal_worst[j] = np.min(weighted_matrix[:, j])
        else:
            ideal_best[j] = np.min(weighted_matrix[:, j])
            ideal_worst[j] = np.max(weighted_matrix[:, j])

    dist_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = score
    df["Rank"] = df["Topsis Score"].rank(ascending=False, method="dense").astype(int)

    return df

def main():
    if len(sys.argv) != 5:
        print("Usage:")
        print("python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print('Example:')
        print('python topsis.py data.xlsx "1,1,1,2" "+,+,-,+" output-result.xlsx')
        sys.exit(1)

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    if not os.path.exists(input_file):
        print("Error: Input file not found")
        sys.exit(1)

    try:
        weights = [float(x) for x in weights_str.split(",")]
    except:
        print("Error: Weights must be numeric and comma separated")
        sys.exit(1)

    impacts = impacts_str.split(",")

    try:
        df = read_file(input_file)
        result = topsis(df, weights, impacts)

        ext_out = os.path.splitext(output_file)[1].lower()
        if ext_out == ".csv":
            result.to_csv(output_file, index=False)
        elif ext_out in [".xlsx", ".xls"]:
            result.to_excel(output_file, index=False)
        else:
            result.to_csv(output_file, index=False)

        print("✅ TOPSIS done successfully!")
        print(f"✅ Output saved to: {output_file}")

    except Exception as e:
        print("Error:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
