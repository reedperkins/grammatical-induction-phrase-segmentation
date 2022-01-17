from collections import Counter
from grammar import addRule, addToken, applyRules, countSubseqIn, getLhs, getRhs, rewriteGrammar, setIn, sortGrammar, substitute

def unused(grammar):
    '''Determine the rules in a grammar that occur less than twice'''
    allRhs = list(getRhs(prod) for prod in grammar)
    for rule in grammar[1:]:
        if sum(countSubseqIn(getLhs(rule), rhs) for rhs in allRhs) < 2:
            yield rule

def drop(grammar, rule):
    '''Return a version of the grammar that does not contain `rule`'''
    return tuple(prod for prod in grammar if prod != rule)

def clean(grammar):
    '''Return a version of the grammar with underutilized rules removed'''
    changed = True
    while changed:
        changed = False
        for lhs, rhs in unused(grammar):
            grammar = drop(grammar, (lhs, rhs))
            grammar = tuple((getLhs(prod), substitute(lhs, rhs, getRhs(prod))) for prod in grammar)
            changed = True
            break
    return grammar

def getDigrams(grammar):
    '''Collect the set of all digrams in the grammar'''
    for prod in grammar:
        rhs = getRhs(prod)
        for i in range(1, len(rhs)):
            yield rhs[i-1], rhs[i]

def maxG(grammar):
    '''Return the number of the most recently added rule. Because sequitur can occasionally 
    prune the grammar, we can't simply take the length of the grammar to determine this
    number'''
    return max(getLhs(prod)[0] for prod in grammar)

def balance(grammar):
    '''Scan the grammar for all digrams. If a digram occurs more than once, add a new
    rule for that digram and replace all occurrences of the digram with a nonterminal'''
    # digramsAndCounts = Counter(d for d in getDigrams(grammar))
    changed = True
    while changed:
        changed = False
        digramsAndCounts = Counter(d for d in getDigrams(grammar))
        for di, count in digramsAndCounts.items():
            if count > 1:
                lhs, rhs = (maxG(grammar)+1,), di
                grammar = tuple((getLhs(prod), substitute(rhs, lhs, getRhs(prod))) for prod in grammar) 
                grammar = addRule(grammar, (lhs, rhs))
                changed = True
                break
    return grammar
    
def addChunk(grammar, chunk):
    '''Append new chunk onto rhs of the start rule'''
    if len(grammar) == 0:
        return addRule(grammar, ((0,), (chunk,)) )
    firstRhs = getRhs(grammar[0])
    return setIn([0, 1], grammar, addToken(firstRhs, chunk) )

def sequitur(seq):
    grammar = tuple()
    for s in seq:
        # print('***')
        # print('s: ', s)
        grammar = addChunk(grammar, s)
        grammar = applyRules(grammar)
        grammar = balance(grammar)
        grammar = clean(grammar)
        # print(stringifyGrammar(grammar))
    return tuple(sortGrammar(rewriteGrammar(grammar)))
    # return grammar