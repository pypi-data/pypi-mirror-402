import sys
import os
import pandas as pd
import numpy as np

def error(msg):
    print("Error:", msg)
    sys.exit(1)


def convert_excel_to_csv(input_file):
    try:
        df = pd.read_excel(input_file, engine="openpyxl")
        csv_file = input_file.rsplit('.', 1)[0] + ".csv"
        df.to_csv(csv_file, index=False)
        print(f"Converted {input_file} to {csv_file}")
        return csv_file
    except Exception as e:
        print("Actual error:", e)
        error("Failed to convert Excel file to CSV.")


def main():
    if len(sys.argv) != 5:
        error("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFile>")


    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]


    if not os.path.exists(input_file):
        error("Input file not found.")


    ext = os.path.splitext(input_file)[1].lower()


    if ext == ".csv":
        df = pd.read_csv(input_file)
    elif ext in [".xlsx", ".xls"]:
        input_file = convert_excel_to_csv(input_file)
        df = pd.read_csv(input_file)
    else:
        error("Unsupported file format.")



    if df.shape[1] < 3:
        error("Input file must contain at least 3 columns.")


    data = df.iloc[:, 1:]


    try:
        data = data.astype(float)
    except:
        error("From 2nd column onwards, values must be numeric.")


    weights = list(map(float, weights.split(",")))
    impacts = impacts.split(",")


    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        error("Number of weights, impacts and columns must be same.")



    for i in impacts:
        if i not in ['+', '-']:
            error("Impacts must be + or -.")


    norm = data / np.sqrt((data ** 2).sum())
    weighted = norm * weights


    ideal_best = []
    ideal_worst = []


    for i, imp in enumerate(impacts):
        if imp == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())



    S_plus = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    S_minus = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))


    score = S_minus / (S_plus + S_minus)


    df["Topsis Score"] = score
    df["Rank"] = df["Topsis Score"].rank(ascending=False, method="dense").astype(int)


    df.to_csv(output_file, index=False)
    print("TOPSIS analysis completed successfully.")

if __name__ == "__main__":
    main()
