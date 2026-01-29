import os
import pandas as pd
import numpy as np

class TopsisError(Exception):
    pass

def topsis(input_file, weights, impacts, output_file):
    if not os.path.exists(input_file):
        raise TopsisError("File not Found")

    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        raise TopsisError("Input file must contain three or more columns")

    data = df.iloc[:, 1:].copy()
    for col in data.columns:
        if not pd.to_numeric(data[col], errors='coerce').notnull().all():
            raise TopsisError("From 2nd column to last column must contain numeric values only")

    data = data.astype(float)

    weights = weights.split(",")
    impacts = impacts.split(",")

    if len(weights) != len(impacts):
        raise TopsisError("Number of weights must be equal to number of impacts")

    if len(weights) != data.shape[1]:
        raise TopsisError("Number of weights, impacts, and number of columns (from 2nd to last) must be same")

    weights = np.array([float(w) for w in weights])

    impacts = [i.strip() for i in impacts]
    for i in impacts:
        if i not in ["+", "-"]:
            raise TopsisError("Impacts must be either +ve or -ve")

    norm = np.sqrt((data**2).sum(axis=0))
    normalized = data / norm

    weighted = normalized * weights

    ideal_best = []
    ideal_worst = []

    for j in range(weighted.shape[1]):
        if impacts[j] == "+":
            ideal_best.append(weighted.iloc[:, j].max())
            ideal_worst.append(weighted.iloc[:, j].min())
        else:
            ideal_best.append(weighted.iloc[:, j].min())
            ideal_worst.append(weighted.iloc[:, j].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = score
    df["Rank"] = df["Topsis Score"].rank(ascending=False, method="dense").astype(int)

    df.to_csv(output_file, index=False)

    return output_file
