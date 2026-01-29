"""One-to-many string comparison helpers."""

from typing import Iterable, Callable


def compare_many(
    target: str, candidates: Iterable[str], comparator: Callable[[str, str], float]
) -> list[tuple[str, float]]:
    """
    Compare a single target string against many candidates using 
    the given comparator that returns a list with a numeric score.

    Args:
        target (str): string to compare
        candidates (Iterable[str]): strings to compare against
        comparator (Callable[[str, str], float]): function returning 
        a numeric score for similarity

    Returns:
        list[tuple[str, float]]: (candidate, score) pairs ordered by 
        descending score (best matches first)

    usage:
        results = compare_many("target string", ["candidate1", "candidate2"], levenshtein_distance)
    """
    scores = [
        (candidate, float(comparator(target, candidate))) for candidate in candidates
    ]
    return sorted(scores, key=lambda pair: pair[1], reverse=True)
