import re
from pathlib import Path
import sys
from typing import Any, DefaultDict, List, Tuple
from music21 import converter
from music21.note import Note # type: ignore
from music21.duration import DurationException # type: ignore
from music21.stream import Part
from dataclasses import dataclass
from collections import defaultdict
from tqdm import tqdm # type: ignore

from common import formatAnnotation, getPickles, loadAnnotationsFile, parseAnnotationStr, splitIndexHeaderFromStr, writePickles

'''For some reason, parsing an abc file line by line and concatenating the
results yields different results than parsing the whole tune. For example,
with Tune index 251, the 5th line is parsed correctly when only the individual
line is parsed. This probably due to the way the abc file was created -- the durations
of the abc notation do not always add up to 4/4 per measure in that particular peice.
My guess is that the ABC parser does its best to fit notes into meausres when it has
more context. In any case, the sequences given to the induction algorithms must match 
the ones that were the source for the annotations, so we produced them the same way here.'''

Span = Tuple[int, int]

def getMetadataForTune(tune: str):
    '''Extract the metadata string from a tune. Assumes that `tune` is an ABC 1.0 
    formatted string (contains no ABC 2.0 metadata lines)'''
    lines = re.split('\r?\n', tune)
    metaLines = (l for l in lines if re.match('^\w:', l))
    return '\n'.join(metaLines)

def getTuneLinesForTune(tune: str):
    '''Return the lines of the tune body. Assumes that `tune` is an ABC 1.0 formatted
    string (contains no ABC 2.0 metadata lines)'''
    lines = re.split('\r?\n', tune)
    tuneLines = (l for l in lines if not re.match('^\w:', l))
    return tuneLines 

def getAnnotationsForTune(tune: str) -> List[List[Span]]:
    '''Generate annotations for a tune. Returned patterns have at least two 
    occurrences in `tune`, and each occurrences spans at least two notes.
    Musical elements other than notes (e.g. rests) are omitted.'''
    metadata, tuneLines = getMetadataForTune(tune), getTuneLinesForTune(tune)
    patterns: DefaultDict[Any, List[Span]] = defaultdict(list)
    indexOffset = 0
    for line in tuneLines:
        sequence = parseTuneStr(metadata + '\n' + line)
        hashableSeq = tuple(s[1:] for s in sequence) # ignore offset
        spanStart, spanEnd = indexOffset, indexOffset + len(sequence)
        patterns[hashableSeq].append((spanStart, spanEnd))
        indexOffset += len(sequence)
    # anns = [spans for seq, spans in patterns.items() if len(spans) > 1 and len(seq) > 1]
    anns = [spans for seq, spans in patterns.items()] 
    return [(i, ann) for i, ann in enumerate(anns)]

def getTunesFromFile(file):
    '''Gets all individual tunes within a single .abc file'''
    with open(file, encoding='utf-8', errors='replace') as f:
        content = f.read()
    for tune in re.split('\r?\n\n+', content):
        tune = tune.strip()
        yield tune
    
def removeAbc2Lines(tune: str):
    '''Removes ABC 2.0 metadata lines'''
    lines = re.split('\r?\n', tune)
    return '\n'.join(t for t in lines if not t.startswith('%%'))

def allTunes(dir: Path):
    '''Gets the text content of every tune in a directory of .abc files'''
    for tuneFile in dir.glob('*'):
        for tune in getTunesFromFile(tuneFile):
            yield removeAbc2Lines(tune)

def getNoteEvent(n: Note):
    '''Extract NoteEvent information from a music21 Note'''
    return (n.offset, n.pitch.midi, n.duration.quarterLength)

def getMusic21PartForTuneLine(tuneLine: str, metadata: str):
    score = converter.parseData(metadata + '\n' + tuneLine, format='abc')
    part: Part = score.parts[0]
    return part

def parseTuneStr(tune: str):
    '''Consumes a tune and produces a list of tuples (o, m, d) where 
            o is the note onset (in quarter notes), '
            m is the note midi number, and 
            d is the note duration (in quarter notes).'''
    seq = []
    metadata, tuneLines = getMetadataForTune(tune), getTuneLinesForTune(tune)
    lineOffset = 0
    for line in tuneLines:
        part = getMusic21PartForTuneLine(line, metadata)
        notes = part.flat.notes
        for n in notes:
            seq.append((n.offset + lineOffset, n.pitch.midi, n.duration.quarterLength))
        lineOffset += part.duration.quarterLength
    return seq

def createSequenceAndAnnotationFiles(dataDir: Path, outputDir: Path):
    '''Create annotations.txt and sequences.txt'''
    annFile = open(outputDir / 'annotations.txt', 'w', encoding='utf-8')
    seqFile = open(outputDir / 'sequences.txt', 'w', encoding='utf-8')
    tunes = enumerate(allTunes(dataDir))
    for i, tune in tqdm(tunes):
        try:
            annotations = getAnnotationsForTune(tune)
        except DurationException:
            continue
        seqFile.write(f'@@@ Tune index: {i}\n' + tune + '\n\n')
        if len(annotations) == 0:
            continue
        formatted = formatAnnotation(annotations)
        annFile.write(f'@@@ Tune index: {i}\n' + formatted + '\n')
    annFile.close()
    seqFile.close()

def loadSequenceFile(path: Path):
    with open(path) as f:
        entries = re.split('\n\n', f.read())[:-1] # remove trailing empty space
    sequences = {}
    print('Loading sequences')
    for e in tqdm(entries):
        index, tuneStr = splitIndexHeaderFromStr(e)
        seq = parseTuneStr(tuneStr)
        sequences[index] = seq
    return sequences

def parse2(tune):
    return converter.parseData(tune,format='abc')

def load2(path: Path):
    with open(path, errors='ignore') as f:
        entries = re.split('\n\n', f.read())[:-1] # remove trailing empty space
    for e in entries:
        index, tuneStr = splitIndexHeaderFromStr(e)
        seq = parse2(tuneStr)
        yield index, seq

if __name__ == '__main__':
    args = sys.argv[1:]
    usage = f'Usage: {__file__} {{pickle, ann}} dataDir [outputDir]'
    if len(args) not in (2, 3):
        raise SystemExit(usage)
    dataPath = Path(args[1])
    if args[0] == 'pickle':
        outputPath = Path(args[2]) if len(args) == 3 else Path(args[1])
        sequences = loadSequenceFile(dataPath / 'sequences.txt')
        annotations = loadAnnotationsFile(dataPath / 'annotations.txt')

        # import random
        # annotations = dict(
        #     random.sample(
        #         list(annotations.items()),
        #         1000
        #     )
        # )

        print('Creating zipped pickle')
        pickles = getPickles(sequences, annotations, 'essen')
        writePickles(pickles, outputPath / 'essen.pkl.gz')
    elif args[0] == 'ann':
        outputPath = Path(args[2]) if len(args) == 3 else Path(args[1]).parent
        createSequenceAndAnnotationFiles(Path(args[1]), outputPath)
    else:
        raise SystemExit(usage)