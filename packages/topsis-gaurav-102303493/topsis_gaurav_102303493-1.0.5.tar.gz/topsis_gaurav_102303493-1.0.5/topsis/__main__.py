import argparse
import sys
import pandas as pd
from topsis import topsis

def main():
    parser = argparse.ArgumentParser(
        description="TOPSIS Method for Multi-Criteria Decision Making"
    )
    parser.add_argument("input_file", help="Input CSV file")
    parser.add_argument("weights", help="Comma separated weights (e.g. 1,1,1,1)")
    parser.add_argument("impacts", help="Comma separated impacts (e.g. +,-,+,-)",type=str)
    parser.add_argument("output_file", help="Output CSV file")

    args = parser.parse_args()

    try:
        decision_matrix = pd.read_csv(args.input_file, index_col=0)
        weights = [float(w.strip()) for w in args.weights.split(",")]
        impacts = [i.strip() for i in args.impacts.split(",")]

        num_columns = len(decision_matrix.columns)

        if len(weights) != num_columns:
            raise ValueError("Number of weights must match number of criteria")

        if len(impacts) != num_columns:
            raise ValueError("Number of impacts must match number of criteria")

        result = topsis(decision_matrix, weights, impacts)
        result = result.reset_index()
        result.to_csv(args.output_file, index=False)

        print("TOPSIS analysis completed successfully.")
        print(f"Output saved to: {args.output_file}")

    except FileNotFoundError:
        print("Error: Input file not found.")
        sys.exit(1)

    except Exception as e:
        print("Unexpected error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
