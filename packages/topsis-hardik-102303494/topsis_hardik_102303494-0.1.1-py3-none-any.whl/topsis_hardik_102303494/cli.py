import sys
import pandas as pd
from topsis_hardik_102303494.topsis import topsis


def main():
    print("TOPSIS CLI WORKING")
    if len(sys.argv) != 5:
        print("Usage: topsis <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    input_file, weights, impacts, output_file = sys.argv[1:]

    weights = list(map(float, weights.split(",")))
    impacts = impacts.split(",")

    df = pd.read_csv(input_file)

    if len(weights) != df.shape[1] - 1:
        print("Error: Weights count mismatch")
        sys.exit(1)

    if len(impacts) != df.shape[1] - 1:
        print("Error: Impacts count mismatch")
        sys.exit(1)

    result = topsis(df, weights, impacts)
    result.to_csv(output_file, index=False)
    print("TOPSIS completed successfully")


if __name__ == "__main__":
    main()
