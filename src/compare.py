from levenshtein import similarity, bandedSimilarity

def greedyIntersection(matchFn, threshold, P, Q):
    '''Compute the intersection of two sets P and Q. Element equality is determined
    using a score function and a threshold.'''
    pMatched = [0]*len(P)
    qMatched = [0]*len(Q)

    for i, p in enumerate(P):
        for j, q in enumerate(Q):
            score = matchFn(p, q)
            if score >= threshold:
                pMatched[i] = 1
                qMatched[j] = 1

    return sum(pMatched), sum(qMatched)

def comparePatterns(scoreFn, A, B):
    score = 0
    for a in A:
        for b in B:
            score = max(score, scoreFn(a, b))
    return score

def extractSubSequences(pattern, seq):
    return set(seq[s:e] for s, e in pattern)

def strictEquality(a, b):
    return 1 if a == b else 0

def compareStrict(A, B):
    return comparePatterns(strictEquality, A, B)

def strictCost(a, b):
    return 0 if a == b else 1

def levenshteinStrict(a, b):
    return similarity(a, b, strictCost)

def bandedLevenshteinStrict(a, b):
    return bandedSimilarity(a, b, strictCost)

def compareLevenshteinStrict(A, B):
    return comparePatterns(levenshteinStrict, A, B)

def compareBandedLevenshteinStrict(A, B):
    return comparePatterns(bandedLevenshteinStrict, A, B)