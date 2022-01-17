from collections import Counter, defaultdict
from re import sub
from typing import DefaultDict
from grammar import addRule, applyRules, countSubseqIn, getRhs, ruleGen, concatify

def _mostFrequent(pairs):
    return max(pairs, default=None, key=lambda p: p[0]) 

def _longestFirst(pairs):
    return max(pairs, default=None, key=lambda p: len(p[1])) 

def _mostCompressive(pairs):
    return max(pairs, default=None, key=lambda p: (p[0] * len(p[1])) - p[0] - len(p[1]) - 1)

def genSubseqs(seq):
    '''Generates a list of all contiguous subsequences of seq up to len(seq) // 2 in length'''
    for i in range(len(seq)):
        for j in range(i + 1, len(seq) + 1):
            yield seq[i:j] 

def getSubseqs(seq):
    return list(genSubseqs(seq))

def getAllSubseqs(grammar):
    '''Generates a list of all contiguous subsequences for the rhs
    of every rule in the grammar'''
    for _, rhs in grammar:
        for s in getSubseqs(rhs):
            yield s

def countInGrammar(seq, grammar):
    '''Count the number of times seq appears in each rhs of the grammar'''
    return sum(countSubseqIn(seq, rhs) for _, rhs in grammar)

def getRepeatsIn(seq, minLength=2, minFreq=2):
    counts = Counter(s for s in genSubseqs(seq) if len(s) >= minLength)
    valids = [(freq, s) for s, freq in counts.items() if freq >= minFreq]
    return valids

# def getAllRepeats(grammar):
#     counts = defaultdict(int)
#     for rhs in map(getRhs, grammar):
#         pairs = list(getRepeatsIn(rhs))
#         for freq, s in pairs:
#             counts[s] += freq
    
#     return ((freq, s) for s, freq in counts.items())

def getRepeats(grammar):
    '''Return a list of all non-overlapping repeated sequences in the right hand sides of all rules in grammar'''
    counts = {}
    for rhs in (getRhs(p) for p in grammar):
        occs = subseqs(rhs)
        for s, os in occs.items():
            if s not in counts:
                counts[s] = len(os)
            else:
                counts[s] += len(os)
    return [(count, s) for s, count in counts.items() if count > 1]

def subseqs(seq):
    occurrences = {}
    for i in range(2, len(seq)+1): # window size
        for j in range(0, len(seq) - i + 1):
            s = seq[j:j+i]
            if s not in occurrences:
                occurrences[s] = [j]
            else:
                if j > (occurrences[s][-1] + len(s) - 1):
                    occurrences[s].append(j)
    return occurrences

def irr(objFn, seq):
    getNextRule = ruleGen()
    lhs = (next(getNextRule),)
    grammar = ((lhs, seq),)
    while True:
        _, rhs = grammar[0]
        # repeats = getRepeatsIn(rhs)
        # c = Counter(getRepeats(grammar))
        # repeats = [(freq, s) for s, freq in c.items() if freq > 1]
        repeats = getRepeats(grammar)
        best = objFn(repeats)
        if not best:
            return grammar
        newRule = ((next(getNextRule),), best[1])
        candidate = addRule(grammar, newRule)
        candidate = applyRules(candidate)

        a = concatify(candidate)
        b = concatify(grammar)
        if len(a) <= len(b):
            grammar = candidate
        else:
            return grammar
        # if len(concatify(candidate)) < len(concatify(grammar)):
        #     grammar = candidate
        # else:
        #     return grammar

def longestFirst(seq):
    return irr(_longestFirst, tuple(seq))
    
def mostCompressive(seq):
    return irr(_mostCompressive, tuple(seq))

def repair(seq):
    return irr(_mostFrequent, tuple(seq))