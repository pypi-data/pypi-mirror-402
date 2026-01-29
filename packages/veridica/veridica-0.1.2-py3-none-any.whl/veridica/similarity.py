"""String similarity measurement functions."""

from collections import defaultdict


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the levenstein distance between two strings"""

    if s1 == s2:
        return 0
    rows = len(s1) + 1
    cols = len(s2) + 1

    if not s1:
        return cols - 1
    if not s2:
        return rows - 1

    prev = None
    cur = range(cols)
    for r in range(1, rows):
        prev, cur = cur, [r] + [0] * (cols - 1)
        for c in range(1, cols):
            deletion = prev[c] + 1
            insertion = cur[c - 1] + 1
            edit = prev[c - 1] + (0 if s1[r - 1] == s2[c - 1] else 1)
            cur[c] = min(edit, deletion, insertion)

    return cur[-1]


def jaccard_distance(s1: str, s2: str) -> float:
    """Calculate the Jaccard distance between two strings."""
    # split on whitespace into token sets
    set1 = set(s1.split())
    set2 = set(s2.split())

    # both empty -> identical
    if not set1 and not set2:
        return 0.0

    intersection = set1 & set2
    union = set1 | set2

    # guard against division by zero (shouldn't happen due to check above)
    if not union:
        return 0.0

    return 1.0 - (len(intersection) / len(union))


def hamming_distance(s1: str, s2: str) -> float:
    """Calculate the Hamming distance between two strings."""
    # ensure length of s1 >= s2
    if len(s2) > len(s1):
        s1, s2 = s2, s1

    # distance is difference in length + differing chars
    distance = len(s1) - len(s2)
    for i, c in enumerate(s2):
        if c != s1[i]:
            distance += 1

    return distance


def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Damerau-Levenshtein distance between two strings."""

    if not isinstance(s1, str):
        return 0
    if not isinstance(s2, str):
        return 0

    len1 = len(s1)
    len2 = len(s2)
    infinite = len1 + len2

    # character array
    da = defaultdict(int)

    # distance matrix
    score = [[0] * (len2 + 2) for x in range(len1 + 2)]

    score[0][0] = infinite
    for i in range(0, len1 + 1):
        score[i + 1][0] = infinite
        score[i + 1][1] = i
    for i in range(0, len2 + 1):
        score[0][i + 1] = infinite
        score[1][i + 1] = i

    for i in range(1, len1 + 1):
        db = 0
        for j in range(1, len2 + 1):
            i1 = da[s2[j - 1]]
            j1 = db
            cost = 1
            if s1[i - 1] == s2[j - 1]:
                cost = 0
                db = j

            score[i + 1][j + 1] = min(
                score[i][j] + cost,
                score[i + 1][j] + 1,
                score[i][j + 1] + 1,
                score[i1][j1] + (i - i1 - 1) + 1 + (j - j1 - 1),
            )
        da[s1[i - 1]] = i

    return score[len1 + 1][len2 + 1]
