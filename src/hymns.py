from pathlib import Path
import re
from itertools import groupby
from operator import itemgetter
from collections import defaultdict
import sys
from music21 import converter

from tqdm.std import tqdm

from common import formatAnnotation, getPickles, loadAnnotationsFile, splitIndexHeaderFromStr, writePickles

def parseAnnotationCsv(annCsv):
    lines = re.split('\r?\n', annCsv)[1:] # ignore header
    labels = (l.split(',')[-1] for l in lines) 
    patterns = defaultdict(list)
    for label, group in groupby(enumerate(labels), key=itemgetter(1)):
        letter, _ = label.split(':')
        items = list(group)
        spanStart, spanEnd = items[0][0], items[-1][0] + 1
        patterns[letter].append((spanStart, spanEnd))
    return [(letter, spans) for letter, spans in patterns.items() if len(spans) > 1]
    
def collectAnnotations(datadir: Path, outdir: Path):
    '''Collect all annotations and put them in a single file. Each annotation contains
    a reference to the original sequence it was derived from.'''
    annFile = open(outdir / 'annotations.txt', 'w')
    seqFile = open(outdir / 'sequences.txt', 'w')
    for i, hymnFolder in enumerate(datadir.glob('*')):
        hymn = hymnFolder.name + '.musicxml'
        seqFile.write(f'@@@ Tune index: {i}\n' + hymn + '\n\n')
        for annCsvFile in hymnFolder.glob('*.csv'):
            with open(annCsvFile) as f:
                annCsv = f.read().strip()
            ann = parseAnnotationCsv(annCsv)
            if len(ann) == 0:
                continue
            formatted = formatAnnotation(ann)
            annFile.write(f'@@@ Tune index: {i}\n' + formatted + '\n')
    annFile.close()
    seqFile.close()

def parseHymnXml(hymnXml: str):
    score = converter.parse(hymnXml)
    notes = score.parts['Soprano'].flat.notes
    seq = [(n.offset, n.pitch.midi, n.duration.quarterLength) for n in notes]
    return seq

def loadSequences(path: Path):
    with open(path) as f:
        entries = re.split('\n\n', f.read())[:-1] # remove trailing empty space
    sequences = {}
    print('Loading sequences')
    for e in tqdm(entries):
        index, hymnFile = splitIndexHeaderFromStr(e)
        with open(path.parent / 'musicxml'/ hymnFile) as f:
            hymnXml = f.read()
        seq = parseHymnXml(hymnXml)
        sequences[index] = seq
    return sequences

def parse2(hymnXml: str):
    score = converter.parse(hymnXml)
    part = score.parts['Soprano']
    return part

def load2(path: Path):
    with open(path) as f:
        entries = re.split('\n\n', f.read())[:-1] # remove trailing empty space
    sequences = {}
    print('Loading sequences')
    for e in tqdm(entries):
        index, hymnFile = splitIndexHeaderFromStr(e)
        with open(path.parent / 'musicxml'/ hymnFile) as f:
            hymnXml = f.read()
        seq = parse2(hymnXml)
        sequences[index] = seq
    return sequences

if __name__ == '__main__':
    args = sys.argv[1:]
    usage = f'Usage: {__file__} {{pickle, ann}} dataDir [outputDir]'
    if len(args) not in (2, 3):
        raise SystemExit(usage)
    dataPath = Path(args[1])
    if args[0] == 'pickle':
        outputPath = Path(args[2]) if len(args) == 3 else Path(args[1])
        sequences = loadSequences(dataPath / 'sequences.txt')
        annotations = loadAnnotationsFile(dataPath / 'annotations.txt')
        print('Creating zipped pickle')
        pickles = getPickles(sequences, annotations, 'hymns')
        writePickles(pickles, outputPath / 'hymns.pkl.gz')
    elif args[0] == 'ann':
        outputPath = Path(args[2]) if len(args) == 3 else Path(args[1]).parent
        collectAnnotations(Path(args[1]), outputPath)
    else:
        raise SystemExit(usage)
