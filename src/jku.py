from pathlib import Path
from glob import glob
import sys
import os
import re

from common import formatAnnotation, getPickles, loadAnnotationsFile, splitIndexHeaderFromStr, writePickles

def findIndex(fn, lst):
    for i, e in enumerate(lst):
        if fn(e):
            return i
    raise RuntimeError('No element found.')

def parseOccContent(content: str):
    lines = re.split('\r?\n', content)
    content = []
    for line in lines:
        data = line[1:-1].split(' ')
        offset = eval(data[0])
        midi = int(data[1])
        content.append((offset, midi))
    return content

def parseSequenceContent(content: str):
    lines = re.split('\r?\n', content)
    content = []
    for line in lines:
        data = line[1:-1].split(' ')
        offset = eval(data[0])
        midi = int(data[1])
        duration = eval(data[3])
        content.append((offset, midi, duration))
    return content

def parseSequenceFromFile(sequencePath: Path):
    with open(sequencePath) as f:
        sequenceContent = f.read().strip()
    sequence = parseSequenceContent(sequenceContent)
    return sequence

def collectAnnotations(datadir: Path, outdir: Path):

    annFile = open(outdir / 'annotations.txt', 'w')
    seqFile = open(outdir / 'sequences.txt', 'w')
    for i, artistFolder in enumerate(datadir.glob('*')):
        # print(os.path.basename(artistFolder))
        sequencePath = Path(glob(os.path.join(artistFolder, 'monophonic', 'lisp', '*.txt'))[0])
        seq = parseSequenceFromFile(sequencePath)
        seqFile.write(f'@@@ Tune index: {i}\n' + str(Path(*sequencePath.parts[-5:])) + '\n\n')

        # Extract annotations
        annotations = []
        annotationFolders = glob(os.path.join(artistFolder, 'monophonic', 'repeatedPatterns', '*', '*'))
        for patternFolder in annotationFolders:
            occurenceFiles = glob(os.path.join(patternFolder, 'occurrences', 'lisp', '*.txt'))
            letter = os.path.basename(patternFolder)
            occurrences = []
            for occFile in occurenceFiles: 
                with open(occFile) as f:
                    occ = parseOccContent(f.read().strip())
                spanStart = findIndex(lambda s: s[0] == occ[0][0], seq)
                spanEnd = findIndex(lambda s: s[0] == occ[-1][0], seq) + 1
                occurrences.append((spanStart, spanEnd))
            if len(occurrences) > 1:
                annotations.append((letter, occurrences))

        formatted = formatAnnotation(annotations)
        annFile.write(f'@@@ Tune index: {i}\n' + formatted + '\n')

    annFile.close()
    seqFile.close()

def loadSequences(path: Path):
    with open(path) as f:
        entries = re.split('\n\n', f.read())[:-1] # remove trailing empty space
    sequences = {}
    print('Loading sequences')
    for e in entries:
        index, jkuFile = splitIndexHeaderFromStr(e)
        with open(path.parent / jkuFile) as f:
            jkuContent = f.read().strip()
        seq = parseSequenceContent(jkuContent)
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
        pickles = getPickles(sequences, annotations, 'jku')
        writePickles(pickles, outputPath / 'jku.pkl.gz')
    elif args[0] == 'ann':
        outputPath = Path(args[2]) if len(args) == 3 else Path(args[1]).parent
        collectAnnotations(Path(args[1]), outputPath)
    else:
        raise SystemExit(usage)