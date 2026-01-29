"""Helper functions for the normalisation of scores when using multiple algorithms. """

def min_max_normalize(sorted_scores):
    """Function to min-max normalise the set of scores(distance) to the range [0, 1]."""
    if not sorted_scores:
        return []
    scores = [pair[1] for pair in sorted_scores]
    min_score = min(scores)
    max_score = max(scores)

    if min_score == max_score:
        return [(pair[0], 1.0) for pair in sorted_scores]
    normalized = [
        (pair[0], (pair[1] - min_score) / (max_score - min_score))
        for pair in sorted_scores
    ]
    return normalized
