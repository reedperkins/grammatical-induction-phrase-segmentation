from collections import defaultdict
import re

def getRhs(rule):
    '''Return the right hand side of a rule'''
    _, rhs = rule
    return rhs

def getLhs(rule):
    '''Return the left hand side of a rule'''
    lhs, _ = rule
    return lhs

def findIn(query, seq):
    '''Returns the index of first occurrence of query in seq, or None otherwise'''
    try:
        return seq.index(query)
    except ValueError:
        return None

def getPairs(seq):
    '''Return the set of all pairs of elements in seq'''
    return set(map(lambda i: (seq[i-1], seq[i]), range(1, len(seq))))

def isPrefixOf(subseq, seq) -> bool:
    '''Determines if subseq constitutes a prefix of seq'''
    return subseq == seq[:len(subseq)]

def stripPrefix(subseq, seq):
    '''Returns seq with prefix subseq removed'''
    if not isPrefixOf(subseq, seq):
        return seq
    return seq[len(subseq):]

def countSubseqIn(subseq, seq):
    '''Returns the number of non-overlapping occurrences of subseq in seq'''
    if len(seq) == 0:
        return 0
    elif isPrefixOf(subseq, seq):
        return 1 + countSubseqIn(subseq, stripPrefix(subseq, seq))
    else:
        return countSubseqIn(subseq, seq[1:])

def addRule(g, newRule):
    '''Returns a new grammar with newRule appended to g'''
    return g + (newRule,)

def addRule2(g, newRule):
    '''Returns a new grammar that contains newRule. If the new rule already exists,
    the original grammar is returns. Otherwise, the new rule is appended to the grammar'''
    result = findIn(newRule, g)
    if result is not None:
        return g
    return addRule(g, newRule)

def addToken(seq, token):
    '''Append a token onto seq'''
    return seq + (token,)

def substitute(source, target, seq):
    '''Returns seq with all non-overlapping occurrences of source replaced with target'''
    if len(seq) == 0:
        return seq
    elif isPrefixOf(source, seq):
        return target + substitute(source, target, stripPrefix(source, seq))
    else:
        return (seq[0],) + substitute(source, target, seq[1:])

def setIn(indices, source, target):
    '''Replace source[i1, i2, ..., iN for i in indices] with target'''
    if len(indices) == 0:
        return target
    i = indices[0]
    return source[:i] + (setIn(indices[1:], source[i], target),) + source[i+1:] 

def applyRule(rule, seq):
    '''Substitutes all occurrences of the rhs of rule in seq with its lhs'''
    rhs, lhs = rule
    return substitute(lhs, rhs, seq)

def applyRules(g):
    '''Returns a new grammar where every rule of g has been applied to
    every other rule of g'''
    for i in range(len(g)):
        target, source = g[i]
        for j in range(len(g)):
            if i == j: continue
            rhs = g[j][1]
            g = setIn([j, 1], g, substitute(source, target, rhs))
    return g

def ruleGen():
    i = 0
    while True:
        yield i
        i += 1

def getGramamrSize(grammar):
    size = 0
    for p in grammar:
        size += len(getRhs(p)) + 1
    return size

def printGrammar(grammar):
    for rule in grammar:
        print(rule)

def parseToken(string):
    '''Converts a string version of a token into an internal representation'''
    nonterminalRegex = r'@(\d+)'
    result = re.match(nonterminalRegex, string)
    if result:
        return int(result.groups()[0])
    return string

def parseRule(string):
    '''Converts a string version of rule into an internal representation'''
    left, right = string.split('->')
    right = map(str.strip, right.split(','))
    right = list(right)
    lhs = parseToken(left)
    rhs = tuple(map(parseToken, right))
    return ((lhs,), rhs)

def fromString(string: str):
    '''Converts a string version of a grammar into an internal representation'''
    lines = string.split('\n')
    grammar = tuple(parseRule(l) for l in lines)
    return grammar

def stringifyToken(token):
    '''Returns the string version of a token in the grammar.
    Nonterminals are represented internally as ints.'''
    if isinstance(token, int):
        return f'@{token}'
    return str(token)

def stringifyRule(rule):
    '''Returns the string version of a production in the grammar'''
    lhs, rhs = rule
    return ''.join(map(stringifyToken, lhs)) + ' -> ' + ','.join(map(stringifyToken, rhs))

def stringifyGrammar(grammar):
    '''Returns the string version of a grammar. Nonterminals are prefixed with an '@' symbol.
    Rules are rendered in the form of 'lhs -> rhs'. '''
    result = []
    for rule in grammar:
        result.append(stringifyRule(rule))
    return '\n'.join(result)

def prettify(grammar):
    '''Returns a string version of grammar with the rules rewritten and sorted in order of
    appearance'''
    return stringifyGrammar(sorted(rewriteGrammar(grammar)))

def sortGrammar(grammar):
    return sorted(grammar, key=lambda rule: rule[0])

def buildLookup(grammar):
    counter = 0
    lookup = {}
    for rule in grammar:
        lhs, rhs = rule
        allSyms = lhs + rhs
        for sym in allSyms:
            if isinstance(sym, int):
                if sym not in lookup:
                    lookup[sym] = counter
                    counter += 1
    return lookup

def rewriteGrammar(grammar):
    lookup = buildLookup(grammar)
    for i, rule in enumerate(grammar):
        lhs, rhs = rule
        newLhs = lookup[lhs[0]],
        newRhs = tuple(map(lambda s: lookup.get(s, s), rhs))
        grammar = setIn([i], grammar, (newLhs, newRhs))
    return grammar

def loadGramamrFromFile(path):
    with open(path) as f:
        grammar = fromString(f.read())
    return grammar

def expand(seq, grammar):
    if len(seq) == 0:
        return []
    result = []
    for s in seq:
        if isinstance(s, int):
            toExpand = [r for r in grammar if getLhs(r) == (s,)][0]
            toExpand = getRhs(toExpand)
            result.extend(expand(toExpand, grammar))
        else:
            result.append(s)
    return tuple(result)
    # first, rest = seq[0], seq[1:]
    # if isinstance(first, int):
    #     toExpand = [r for r in grammar if getLhs(r) == (first,)][0]
    #     toExpand = getRhs(toExpand)
    #     expanded = expand(toExpand, grammar, result)
    # else:
    #     expanded = (first,)
    # return expand(rest, grammar, result + expanded)

def findOccurrencesIn(subSeq, seq):
    if len(subSeq) == 0:
        return () 
    elif len(seq) == 0:
        return () 
    i = 0
    results = ()
    while i < len(seq):
        if isPrefixOf(subSeq, seq[i:]):
            results = results + ((i, i+len(subSeq)),)
            i += len(subSeq)
        else:
            i += 1
    return results


    # elif isPrefixOf(subSeq, seq):
    #     result = result + (index, index + len(subSeq))
    #     return findOccurrencesIn(subSeq, stripPrefix(subSeq, seq), index+len(subSeq))
    # else:
    #     return findOccurrencesIn(subSeq, seq[1:], result, index+1)

def convertGrammarToAnnotation(g):
    startRule, rest = g[0], g[1:]
    seq = expand(getRhs(startRule), g)
    annotations = []
    for _, rhs in rest:
        expanded = expand(rhs, g)
        spans = findOccurrencesIn(expanded, seq)
        annotations.append(spans)
    return annotations

def convertGrammarToAnnotation2(g):
    startRule = getRhs(g[0])
    patterns = defaultdict(list)
    index = 0
    for sym in startRule:
        if isinstance(sym, int):
            length = len(expand([sym], g))
            patterns[sym].append((index, index+length))
            index += length
        else:
            index += 1
    return [spans for spans in patterns.values()]




def concatify(grammar):
    result = []
    for _, rhs in grammar:
        result.extend([*(rhs + ('#', ))])
    return tuple(result)

