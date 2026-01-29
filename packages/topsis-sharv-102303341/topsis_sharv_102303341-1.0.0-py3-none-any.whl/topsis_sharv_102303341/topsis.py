import sys
import pandas as pd
from topsispy import topsis


def error(msg):
    print("Error:", msg)
    sys.exit(1)


def read_input_file(file):
    if file.endswith(".csv"):
        return pd.read_csv(file)
    elif file.endswith(".xlsx"):
        return pd.read_excel(file)
    else:
        error("Only CSV or Excel (.xlsx) files are supported")


def main():
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <inputFile> <weights> <impacts> <outputFile>")
        error("Incorrect number of arguments")

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    try:
        df = read_input_file(input_file)
    except FileNotFoundError:
        error("Input file not found")
    except Exception as e:
        error(f"Error reading file: {e}")

    if df.shape[1] < 3:  # type: ignore
        error("Input file must contain at least 3 columns")

    # Take columns from 2nd to last
    data = df.iloc[:, 1:]  # type: ignore

    try:
        data = data.apply(pd.to_numeric)
    except:
        error("Columns from 2nd to last must be numeric")

    weights = weights_str.split(",")
    impacts = impacts_str.split(",")

    if len(weights) != len(impacts) or len(weights) != data.shape[1]:
        error("Number of weights, impacts, and criteria must be same")

    try:
        weights = [float(w) for w in weights]
    except:
        error("Weights must be numeric")

    for imp in impacts:
        if imp not in ['+', '-']:
            error("Impacts must be either + or -")

    # ---- TOPSIS calculation----
    try:
        result = topsis(data.values, weights, impacts)

        if isinstance(result, tuple):
            scores = result[1]
        else:
            scores = result


    except Exception as e:
        error(f"Error in TOPSIS calculation: {e}")

    df["Topsis Score"] = scores  # type: ignore
    df["Rank"] = df["Topsis Score"].rank( # type: ignore
        ascending=False).astype(int)  # type: ignore

    df.to_csv(output_file, index=False)  # type: ignore
    print("TOPSIS result saved to:", output_file)


if __name__ == "__main__":
    main()
