from functools import partial
from itertools import chain, product
from tqdm import tqdm
from pathlib import Path
from multiprocessing import Pool
import pickle
import gzip
import sys

from common import  gzPickleIter
from sequitur import sequitur
from lzw import lz78
from irr import repair, mostCompressive, longestFirst
from grammar import convertGrammarToAnnotation2, concatify
from viewpoint import midi, duration, interOnsetInterval, pitchContour, pitchInterval, createViewpointFn
from viewpoint import powerset
from compare import compareLevenshteinStrict, greedyIntersection

DATASET_DIR = Path('datasets')
essenPath = DATASET_DIR / 'essen' / 'essen1000.pkl.gz'
jkuPath = DATASET_DIR / 'jku' / 'jku.pkl.gz'
hymnsPath = DATASET_DIR / 'hymns' / 'hymns.pkl.gz'

def runJob(job):
    alg, vpSeq, gt, cmpFn, *info  = job
    grammar = alg(vpSeq)
    discovered = convertGrammarToAnnotation2(grammar)

    # discovered = [d for d in discovered if len(d) > 1]
    # discovered = gt # sanity check 
    P = [tuple(vpSeq[s:e] for s, e in p) for p in gt]
    Q = [tuple(vpSeq[s:e] for s, e in p) for p in discovered]

    if len(Q) == 0:
        precision, recall = 0.0, 0.0
    else:
        pMatched, qMatched = cmpFn(P, Q)
        precision = qMatched / len(Q)
        recall = pMatched / len(P)
    compRatio = len(concatify(grammar)) / len(vpSeq)
    return (precision, recall, compRatio, *info)

def createAllJobs():
    data = chain(
        gzPickleIter(essenPath),
        gzPickleIter(jkuPath),
        gzPickleIter(hymnsPath)
    )

    algorithms = (lz78, repair, mostCompressive, longestFirst, sequitur)
    viewpoints = (midi, duration, interOnsetInterval, pitchContour, pitchInterval)
    vpFns = (createViewpointFn(vpComb) for vpComb in powerset(viewpoints))
    threshold = 0.8
    matchFn = compareLevenshteinStrict
    cmpFn = partial(greedyIntersection, matchFn)

    for data, alg, vp in product(data, algorithms, vpFns):
        seq, ann, datasetName, index = data
        seq = tuple(vp(seq))
        cmpFnT = partial(cmpFn, threshold)
        info = (
            alg.__name__,
            matchFn.__name__,
            threshold,
            vp.__name__,
            datasetName,
            index
        )
        yield alg, seq, ann, cmpFnT, *info

def runJobs(dataPath: Path, outputPath: Path):
    jobs = gzPickleIter(dataPath)

    total = 0
    job2 = gzPickleIter(dataPath)
    for _ in job2:
        total += 1
 
    outFs = gzip.open(outputPath, 'wt')
    with Pool() as p:
        for result in tqdm(p.imap_unordered(runJob, jobs), total=total):
            strResult = map(str, result)
            outFs.write(','.join(strResult) + '\n')           
    # for job in tqdm(jobs):
    #     result = runJob(job)
    #     strResult = map(str, result)
    #     outFs.write(','.join(strResult) + '\n')
    outFs.close()

def writeJobsToFile(allJobs, filename):
    with gzip.open(filename, 'wb') as f:
        for j in tqdm(allJobs):
            f.write(pickle.dumps(j))

if __name__ == '__main__':
    args = sys.argv[1:]
    usage = f'Usage: {__file__} {{create, run}} dataDir [outputDir]'
    if len(args) not in (2, 3):
        raise SystemExit(usage)
    dataPath = Path(args[1])
    outputPath = Path(args[2]) if len(args) == 3 else Path(args[1])
    if args[0] == 'create':
        if dataPath.is_file():
            raise SystemExit(f'Filename {dataPath} already exists')
        allJobs = createAllJobs()
        writeJobsToFile(allJobs, outputPath)
    elif args[0] == 'run':
        # if outputPath.is_file():
        #     raise SystemExit(f'Filename {outputPath} already exists')
        runJobs(dataPath, outputPath)
    else:
        raise SystemExit(usage)
