import argparse
import sys
import pandas as pd
import numpy as np

def topsis(decision_matrix, weights, impacts):
    norm_matrix = decision_matrix.div(np.sqrt(decision_matrix**2).sum(axis=0), axis=1)
    weighted_matrix = norm_matrix * weights
    ideal_best = []
    ideal_worst = []

    for i,impact in enumerate(impacts):
        if impact == '+':
            ideal_best.append(weighted_matrix.iloc[:,i].max())
            ideal_worst.append(weighted_matrix.iloc[:,i].min())
        elif impact == '-':
            ideal_best.append(weighted_matrix.iloc[:,i].min())
            ideal_worst.append(weighted_matrix.iloc[:,i].max())
    
    distance_best = np.sqrt(((weighted_matrix - ideal_best)**2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_matrix - ideal_worst)**2).sum(axis=1))

    topsis_score = distance_worst / (distance_best + distance_worst)

    ranks = topsis_score.rank(ascending=False, method='dense').astype(int)

    result = decision_matrix.copy()
    result['Topsis Score'] = topsis_score
    result['Rank'] = ranks

    return result

def main():
    parser = argparse.ArgumentParser(description='TOPSIS Method for Multi-Criteria Decision Making')
    parser.add_argument('input_file')
    parser.add_argument('weights')
    parser.add_argument('impacts')
    parser.add_argument('output_file')

    args = parser.parse_args()

    try:
        decision_matrix = pd.read_csv(args.input_file, index_col=0)
        weights = [float(w.strip()) for w in args.weights.split(',')]
        impacts = [i.strip() for i in args.impacts.split(',')]

        num_columns = len(decision_matrix.columns)
        if len(weights) != num_columns:
            raise ValueError("number of weights must match number of criteria")
        if len(impacts) != num_columns:
            raise ValueError("number of impacts must match number of criteria")
        
        result = topsis(decision_matrix, weights, impacts)
        result = result.reset_index()
        result.to_csv(args.output_file, index=False)

    except Exception as e:
        print("unexpected error ",e)
        sys.exit(1)

    except FileNotFoundError:
        print("file not found")
        sys.exit(1)

if __name__ == "__main__":
    main()