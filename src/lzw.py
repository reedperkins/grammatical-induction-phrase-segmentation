from grammar import ruleGen, findIn, setIn, getLhs, getRhs, addRule, addToken, applyRules

def getCodeFor(grammar, seq):
    if len(seq) == 1:
        return seq
    ruleIndex = findIn(seq, list(map(getRhs, grammar)))
    return getLhs(grammar[ruleIndex])

def appendToStartRule(grammar, seq):
    return setIn([0, 1], grammar, grammar[0][1] + seq)

def phraseExists(grammar, phrase):
    return findIn(phrase, list(map(getRhs, grammar)))

def lzw(seq, balanceAfter=True):
    getNextRule = ruleGen()
    grammar = ((next(getNextRule),), ()),
    curPhrase = seq[0],
    for t in seq[1:]:
        newPhrase = addToken(curPhrase, t)
        if phraseExists(grammar, newPhrase):
            curPhrase = newPhrase
        else:
            grammar = appendToStartRule(grammar, getCodeFor(grammar, curPhrase))
            newRule = ((next(getNextRule),), newPhrase)
            grammar = addRule(grammar, newRule)
            curPhrase = t,
    grammar = appendToStartRule(grammar, getCodeFor(grammar, curPhrase))
    if balanceAfter:
        grammar = applyRules(grammar)
    return grammar

def lz78(seq):
    grammar = ( ((0,), ()), )
    rule = 1
    lookup = {}
    buffer = ()
    for s in seq:
        buffer = addToken(buffer, s)
        if buffer not in lookup:
            newRule = ((rule,), buffer)
            grammar = appendToStartRule(grammar, (rule,))
            grammar = addRule(grammar, newRule)
            lookup[buffer] = (rule,)
            rule += 1
            buffer = ()
        else:
            buffer = lookup.get(buffer)
    if buffer:
        grammar = appendToStartRule(grammar, buffer)
    return grammar


