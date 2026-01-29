import pandas as pd
import numpy as np

def topsis(decision_matrix, weights, impacts):
    norm_matrix = decision_matrix.div(np.sqrt((decision_matrix**2).sum(axis=0)), axis=1)
    weighted_matrix = norm_matrix * weights

    ideal_best = []
    ideal_worst = []

    for i, impact in enumerate(impacts):
        if impact == '+':
            ideal_best.append(weighted_matrix.iloc[:, i].max())
            ideal_worst.append(weighted_matrix.iloc[:, i].min())
        elif impact == '-':
            ideal_best.append(weighted_matrix.iloc[:, i].min())
            ideal_worst.append(weighted_matrix.iloc[:, i].max())
        else:
            raise ValueError("Impact must be either '+' or '-'")

    distance_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    topsis_score = distance_worst / (distance_best + distance_worst)
    ranks = topsis_score.rank(ascending=False, method='dense').astype(int)

    result = decision_matrix.copy()
    result['Topsis Score'] = topsis_score
    result['Rank'] = ranks

    return result
