from functools import partial
from itertools import chain, combinations

# NoteEvents are tuples of the form (onset, midiNote, duration)

def onset(noteEvent, *args):
    return noteEvent[0]

def midi(noteEvent, *args):
    return noteEvent[1]

def duration(noteEvent, *args):
    return noteEvent[2]

def interOnsetInterval(noteEvent, index, seq):
    if index == 0:
        return None
    prevNoteEvent = seq[index-1]
    return onset(noteEvent) - onset(prevNoteEvent) 
    
def pitchContour(noteEvent, index, seq):
    if index == 0:
        return None
    prevNoteEvent = seq[index-1]
    return 1 if midi(noteEvent) > midi(prevNoteEvent) else 0 if midi(noteEvent) == midi(prevNoteEvent) else -1

def pitchInterval(noteEvent, index, seq):
    if index == 0:
        return None
    prevNoteEvent = seq[index-1]
    return midi(noteEvent) - midi(prevNoteEvent)

def applyVps(vps, seq):
    for i, s in enumerate(seq):
        yield tuple(vp(s, i, seq) for vp in vps)

def createViewpointFn(vps):
    f = partial(applyVps, vps)
    f.__name__ = ' '.join(sorted(v.__name__ for v in vps))
    return f

def powerset(seq):
    '''Returns a powerset of seq without the empty set'''
    s = list(seq)
    return chain.from_iterable(combinations(s, r) for r in range(1, len(s) + 1))