import sys
import os
import pandas as pd
import numpy as np

def error_and_exit(msg):
    print("Error:", msg)
    sys.exit(1)

def parse_weights(wstr):
    parts = [p.strip() for p in wstr.split(',')]
    if len(parts) == 0:
        error_and_exit("Weights must be comma separated values")
    weights = []
    for p in parts:
        try:
            weights.append(float(p))
        except:
            error_and_exit("Weights must be numeric and comma separated")
    return np.array(weights, dtype=float)

def parse_impacts(istr):
    parts = [p.strip() for p in istr.split(',')]
    if len(parts) == 0:
        error_and_exit("Impacts must be comma separated values")
    impacts = []
    for p in parts:
        if p == '':
            error_and_exit("Impacts contain empty value")
        first = p[0]
        if first not in ['+','-']:
            if p.lower().startswith('+ve') or p.lower().startswith('-ve'):
                first = p[0]
            else:
                error_and_exit("Impacts must be either + or - (or +ve / -ve)")
        impacts.append(first)
    return impacts

def read_and_validate_csv(filename):
    if not os.path.isfile(filename):
        error_and_exit("File not found: " + filename)
    try:
        df = pd.read_csv(filename)
    except Exception as e:
        error_and_exit("Failed to read CSV file: " + str(e))
    if df.shape[1] < 3:
        error_and_exit("Input file must contain three or more columns")
    return df

def ensure_numeric(df, cols):
    sub = df.iloc[:, cols].apply(pd.to_numeric, errors='coerce')
    if sub.isnull().any().any():
        error_and_exit("Non-numeric data found in criteria columns")
    return sub.astype(float)

def compute_topsis(data_mat, weights, impacts):
    norm_denom = np.sqrt((data_mat ** 2).sum(axis=0))
    if (norm_denom == 0).any():
        error_and_exit("At least one criterion column has all zeros; cannot normalize")
    norm_mat = data_mat / norm_denom
    weighted = norm_mat * weights
    ideal_best = np.zeros(weighted.shape[1])
    ideal_worst = np.zeros(weighted.shape[1])
    for j, imp in enumerate(impacts):
        if imp == '+':
            ideal_best[j] = weighted[:, j].max()
            ideal_worst[j] = weighted[:, j].min()
        else:
            ideal_best[j] = weighted[:, j].min()
            ideal_worst[j] = weighted[:, j].max()
    s_pos = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    s_neg = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))
    with np.errstate(divide='ignore', invalid='ignore'):
        score = s_neg / (s_pos + s_neg)
    score = np.nan_to_num(score)
    return score

def main():
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights(comma separated)> <Impacts(comma separated)> <ResultFileName>")
        sys.exit(1)
    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    result_file = sys.argv[4]
    df = read_and_validate_csv(input_file)
    num_criteria = df.shape[1] - 1
    weights = parse_weights(weights_str)
    impacts = parse_impacts(impacts_str)
    if len(weights) != num_criteria:
        error_and_exit("Number of weights must be equal to number of criteria columns (from 2nd to last). Expected " + str(num_criteria))
    if len(impacts) != num_criteria:
        error_and_exit("Number of impacts must be equal to number of criteria columns (from 2nd to last). Expected " + str(num_criteria))
    criteria_data = ensure_numeric(df, list(range(1, df.shape[1])))
    data_mat = criteria_data.values
    score = compute_topsis(data_mat, weights, impacts)
    df['Topsis Score'] = np.round(score, 6)
    df['Rank'] = df['Topsis Score'].rank(method='max', ascending=False).astype(int)
    try:
        df.to_csv(result_file, index=False)
    except Exception as e:
        error_and_exit("Failed to write result file: " + str(e))
    print("Output written to", result_file)

if __name__ == "__main__":
    main()
