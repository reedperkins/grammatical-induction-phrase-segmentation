import gzip
import pickle
from pathlib import Path
import re
from collections import defaultdict


def getPickles(sequences, annotations, datasetName):
    for index, ann in annotations.items():
        seq = sequences[index]
        yield pickle.dumps((seq, ann, datasetName, index))

def writePickles(data, outputPath: Path):
    with gzip.open(outputPath, 'wb') as f:
        for d in data:
            f.write(d)


def gzPickleIter(path: Path):
    with gzip.open(path) as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break

def pickleIterFs(filestream):
    while True:
        try:
            yield pickle.load(filestream)
        except EOFError:
            break

def pickleIter(path: Path):
    '''Incrementally yield separate pickles from a pickle file.'''
    with open(path, 'rb') as pkl:
        while True:
            try:
                yield pickle.load(pkl)
            except EOFError:
                break 

def getPatterns(lines):
    spans = []
    for line in lines:
        if line.startswith('Pattern'):
            if len(spans) > 0:
                yield spans
            spans = []
        else:
            start, end = re.search(r'(\d+):(\d+)', line).groups()
            spans.append((int(start), int(end)))
    yield spans

def parseAnnotationStr(annotation: str):
    lines = re.split('\r?\n', annotation)
    spans = [p for p in getPatterns(lines)]
    return spans

def splitIndexHeaderFromStr(strWithIndexHeader: str):
    lines = re.split(r'\r?\n', strWithIndexHeader)
    index = int(lines[0].split(': ')[1])
    strNoIndexHeader = '\n'.join(lines[1:])
    return index, strNoIndexHeader

def loadAnnotationsFile(path: Path):
    with open(path) as f:
        entries = re.split('\n\n', f.read())[:-1] # remove trailing empty space
    annotations = defaultdict(list)
    for e in entries:
        index, annStr = splitIndexHeaderFromStr(e)
        ann = parseAnnotationStr(annStr)
        annotations[index].extend(ann)
    return annotations

def formatAnnotation(ann):
    '''Render annotations into a string.'''
    result = ''
    for identifier, pattern in ann:
        if isinstance(identifier, int):
            result += f'Pattern {identifier+1}:\n'
        else:
            result += f'Pattern {identifier}:\n'
        for spanStart, spanEnd in pattern:
            result += f'\tSpan {spanStart}:{spanEnd}\n'
    return result

def formatAnnotation2(ann):
    '''Render annotations into a string.'''
    result = ''
    for identifier, pattern in ann:
        if isinstance(identifier, int):
            result += f'Pattern {identifier+1}:\n'
        else:
            result += f'Pattern {identifier}:\n'
        for spanStart, spanEnd in pattern:
            result += f'\tSpan {spanStart}:{spanEnd}\n'
    return result             