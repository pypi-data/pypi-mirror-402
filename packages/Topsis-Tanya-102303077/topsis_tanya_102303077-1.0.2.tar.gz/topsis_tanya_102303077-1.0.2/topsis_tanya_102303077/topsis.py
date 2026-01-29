import sys
import os
import pandas as pd
import numpy as np

def error(msg):
    print("Error:", msg)
    sys.exit(1)

def main():
    if len(sys.argv) != 5:
        error("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFileName>")

    inp = sys.argv[1]
    w_str = sys.argv[2]
    imp_str = sys.argv[3]
    out = sys.argv[4]

    if not os.path.isfile(inp):
        error("Input file not found")

    try:
        df = pd.read_csv(inp)
    except:
        error("Cannot read input file")

    if df.shape[1] < 3:
        error("Input file must have at least three columns")

    data = df.iloc[:, 1:]

    if not np.all(data.applymap(np.isreal)):
        error("Columns from 2nd onward must be numeric")

    try:
        w = list(map(float, w_str.split(',')))
        imp = imp_str.split(',')
    except:
        error("Weights and impacts must be comma separated")

    if len(w) != data.shape[1] or len(imp) != data.shape[1]:
        error("Number of weights, impacts and columns must be same")

    for i in imp:
        if i not in ['+', '-']:
            error("Impacts must be + or -")

    norm = data / np.sqrt((data ** 2).sum())
    w_norm = norm * w

    best = []
    worst = []

    for i in range(len(imp)):
        if imp[i] == '+':
            best.append(w_norm.iloc[:, i].max())
            worst.append(w_norm.iloc[:, i].min())
        else:
            best.append(w_norm.iloc[:, i].min())
            worst.append(w_norm.iloc[:, i].max())

    best = np.array(best)
    worst = np.array(worst)

    d_best = np.sqrt(((w_norm - best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((w_norm - worst) ** 2).sum(axis=1))

    score = d_worst / (d_best + d_worst)

    df["Topsis Score"] = score.round(4)
    df["Rank"] = df["Topsis Score"].rank(ascending=False, method="dense").astype(int)

    df.to_csv(out, index=False)
    print("Result saved in", out)
    
def run():
    main()
    
if __name__ == "__main__":
    main()