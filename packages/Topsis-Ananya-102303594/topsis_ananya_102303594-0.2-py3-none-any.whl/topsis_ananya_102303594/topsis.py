import sys
import pandas as pd
import numpy as np
import os

def stop(msg):
    print("Error:", msg)
    sys.exit(1)

def read_file(name):
    if not os.path.exists(name):
        stop("Input file not found")
    try:
        df = pd.read_csv(name)
    except:
        stop("Unable to read input file")
    if df.shape[1] < 3:
        stop("Input file must contain at least 3 columns")
    return df

def check_numeric(data):
    for c in data.columns:
        if not np.issubdtype(data[c].dtype, np.number):
            stop("Columns from 2nd to last must be numeric")

def get_weights(w, n):
    try:
        w = [float(i) for i in w.split(",")]
    except:
        stop("Weights must be numeric")
    if len(w) != n:
        stop("Number of weights mismatch")
    return w

def get_impacts(i, n):
    i = i.split(",")
    if len(i) != n:
        stop("Number of impacts mismatch")
    for x in i:
        if x not in ["+", "-"]:
            stop("Impacts must be + or -")
    return i

def normalize(data):
    out = data.copy()
    for c in out.columns:
        out[c] = out[c] / np.sqrt((out[c] ** 2).sum())
    return out

def apply_weights(data, w):
    out = data.copy()
    for i in range(len(w)):
        out.iloc[:, i] = out.iloc[:, i] * w[i]
    return out

def ideal_values(data, impacts):
    best = []
    worst = []
    for i in range(len(impacts)):
        col = data.iloc[:, i]
        if impacts[i] == "+":
            best.append(col.max())
            worst.append(col.min())
        else:
            best.append(col.min())
            worst.append(col.max())
    return best, worst

def distances(data, best, worst):
    d_best = []
    d_worst = []
    for i in range(len(data)):
        d_best.append(np.sqrt(((data.iloc[i] - best) ** 2).sum()))
        d_worst.append(np.sqrt(((data.iloc[i] - worst) ** 2).sum()))
    return d_best, d_worst

def scores(d_best, d_worst):
    s = []
    for i in range(len(d_best)):
        s.append(d_worst[i] / (d_best[i] + d_worst[i]))
    return s

def topsis():
    if len(sys.argv) != 5:
        stop("Usage: topsis <InputFile> <Weights> <Impacts> <OutputFile>")

    inp = sys.argv[1]
    w = sys.argv[2]
    im = sys.argv[3]
    out = sys.argv[4]

    df = read_file(inp)
    data = df.iloc[:, 1:]

    check_numeric(data)
    weights = get_weights(w, data.shape[1])
    impacts = get_impacts(im, data.shape[1])

    n = normalize(data)
    wdata = apply_weights(n, weights)
    best, worst = ideal_values(wdata, impacts)
    d1, d2 = distances(wdata, best, worst)
    sc = scores(d1, d2)

    df["Topsis Score"] = sc
    df["Rank"] = df["Topsis Score"].rank(ascending=False).astype(int)
    df.to_csv(out, index=False)

    print("TOPSIS analysis completed")

if __name__ == "__main__":
    topsis()
