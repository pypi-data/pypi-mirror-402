"""
Core TOPSIS algorithm implementation.
"""

import numpy as np

def topsis(matrix, weights, impacts):
    
    """
    Parameters:
        matrix  : 2D numpy array (alternatives × criteria)
        weights : list of floats
        impacts : list of '+' or '-'

    Returns:
        scores : numpy array
        ranks  : numpy array
    """
    matrix = np.array(matrix, dtype=float)
    weights = np.array(weights, dtype=float)
    impacts = np.array(impacts)

    # Step 1: Normalize the decision matrix
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized_matrix = matrix / norm

    # Step 2: Apply weights
    weighted_matrix = normalized_matrix * weights

    # Step 3: Determine ideal best and worst
    ideal_best = np.zeros(weighted_matrix.shape[1])
    ideal_worst = np.zeros(weighted_matrix.shape[1])

    for i in range(weighted_matrix.shape[1]):
        if impacts[i] == '+':
            ideal_best[i] = weighted_matrix[:, i].max()
            ideal_worst[i] = weighted_matrix[:, i].min()
        else:
            ideal_best[i] = weighted_matrix[:, i].min()
            ideal_worst[i] = weighted_matrix[:, i].max()

    # Step 4: Calculate distances
    distance_best = np.sqrt(((weighted_matrix - ideal_best) ** 2).sum(axis=1))
    distance_worst = np.sqrt(((weighted_matrix - ideal_worst) ** 2).sum(axis=1))

    # Step 5: Calculate TOPSIS score
    scores = distance_worst / (distance_best + distance_worst)

    # Step 6: Calculate ranks (higher score = better rank)
    ranks = scores.argsort()[::-1].argsort() + 1

    return scores, ranks

