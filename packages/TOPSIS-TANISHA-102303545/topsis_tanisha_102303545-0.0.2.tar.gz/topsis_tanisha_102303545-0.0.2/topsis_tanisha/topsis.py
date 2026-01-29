import sys
import os
import pandas as pd
import numpy as np


def get_weights(weight_string):
    try:
        return [float(w) for w in weight_string.split(",")]
    except:
        raise ValueError("Weights must be numeric and comma-separated")


def get_impacts(impact_string):
    impacts = impact_string.split(",")
    for i in impacts:
        if i not in ["+", "-"]:
            raise ValueError("Impacts must be either + or -")
    return impacts


def load_dataset(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("Input file not found")

    if file_path.lower().endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.lower().endswith(".xlsx"):
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        raise ValueError("Unsupported file format")

    return df


def check_dataset(df, weights, impacts):
    if df.shape[1] < 3:
        raise ValueError("Input file must contain at least 3 columns")

    criteria = df.iloc[:, 1:]

    for col in criteria.columns:
        if not pd.api.types.is_numeric_dtype(criteria[col]):
            raise ValueError("From 2nd to last columns must contain numeric values only")

    if len(weights) != len(impacts) or len(weights) != criteria.shape[1]:
        raise ValueError(
            "Number of weights, impacts and criteria columns must be same"
        )


def perform_topsis(df, weights, impacts):
    data = df.iloc[:, 1:].values.astype(float)

    norm = np.sqrt((data ** 2).sum(axis=0))
    normalized_data = data / norm

    weighted_data = normalized_data * np.array(weights)

    ideal_best = []
    ideal_worst = []

    for j in range(len(weights)):
        if impacts[j] == "+":
            ideal_best.append(weighted_data[:, j].max())
            ideal_worst.append(weighted_data[:, j].min())
        else:
            ideal_best.append(weighted_data[:, j].min())
            ideal_worst.append(weighted_data[:, j].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    distance_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    return distance_worst / (distance_best + distance_worst)


def main():
    import sys
    import pandas as pd

    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = list(map(float, sys.argv[2].split(",")))
    impacts = sys.argv[3].split(",")
    output_file = sys.argv[4]

    
    if input_file.endswith(".csv"):
        df = pd.read_csv(input_file)
    elif input_file.endswith(".xlsx"):
        df = pd.read_excel(input_file)
    else:
        print("Error: Unsupported file format")
        sys.exit(1)

    
    check_dataset(df, weights, impacts)

    
    scores = perform_topsis(df, weights, impacts)

    
    df["Topsis Score"] = scores
    df["Rank"] = df["Topsis Score"].rank(
        ascending=False, method="dense"
    ).astype(int)

    
    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully")
    print(f"Output saved to {output_file}")

if __name__ == "__main__":
    import pandas as pd

    input_file = "data.xlsx"
    weights = [1, 1, 1, 1, 1]
    impacts = ["+", "+", "+", "+", "+"]
    output_file = "output.csv"

    df = pd.read_excel(input_file)

    check_dataset(df, weights, impacts)
    scores = perform_topsis(df, weights, impacts)

    df["Topsis Score"] = scores
    df["Rank"] = df["Topsis Score"].rank(
        ascending=False, method="dense"
    ).astype(int)

    df.to_csv(output_file, index=False)
    print(" output.csv created")
