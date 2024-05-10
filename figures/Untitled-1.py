# %%
import sys
sys.path.append('../src/')

from lzw import lz78
from sequitur import sequitur
from irr import repair, mostCompressive, longestFirst
from viewpoint import createViewpointFn, duration
from common import gzPickleIter
from pathlib import Path
import gzip
import os
import re
import shutil
import json
import bs4
import subprocess
from functools import reduce
from itertools import islice, groupby
from common import loadHymnAnnotations, formatAnnotation
from PIL import Image

# Configure file paths
DATASETS = Path('../datasets')
HYMNS = Path(DATASETS / 'hymns' / 'hymns.pkl.gz')
RESULTS = Path('../resultst70.gz')
MSCORE = Path(r'C:\Program Files\MuseScore 3\bin\MuseScore3.exe')
CHROME = Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
tempPath = Path('__tmp__')
svgsPath = Path('svgs')
templatePath = Path('src/template.txt')
screenshotsPath = Path('screenshots')

# %%
# Define data pipeline operations

def compose(*args):
    return reduce(lambda x, y: y(x), list(args))

def gzLineIter(path):
    with gzip.open(path, 'rt') as gz:
        for line in gz:
        # for line in islice(gz, 5):
            yield line

def toDicts(lines):
    for line in lines:
        line = line.strip()
        precision, recall, compRatio, algName, cmpFnName, threshold, vpComb, datasetName, index = line.split(',')
        yield {
            'precision': round(float(precision), 2),
            'recall': round(float(recall), 2),
            'compRatio': round(float(compRatio), 2),
            'algName': algName,
            'cmpFnName': cmpFnName,
            'threshold': float(threshold),
            'vpComb': tuple(sorted(vpComb.split(' '))),
            'datasetName': datasetName,
            'index': int(index)
        }

def printObjs(objs):
    for o in objs:
        print(o)


# %% [markdown]
# # Hymn annotations
# 
# Show the ground truth annotations and the discovered annotations for two scenarios:
# 1. A hymn where all algorithms received a positive F1 score
# 2. A hymn where all algorithms received an F1 score of 0

# %%
# Find a hymn where all algorithms received a positive F1 score
# We'll pick the hymns with the highest and lowest average F1 scores across all algorithms using the duration viewpoint

pipeline = compose(
    RESULTS, 
    gzLineIter, 
    toDicts,
    lambda results: filter(lambda result: result['datasetName'] == 'hymns' and result['vpComb'] == ('duration',), results),
    lambda results: sorted(results, key=lambda result: result['index']),
    lambda results: groupby(results, lambda result: result['index'])
)

def f1(prec, rec):
    if prec + rec == 0:
        return 0
    return 2 * prec * rec / (prec + rec)

best = None, 0
worst = None, float('inf')

for index, results in pipeline:
    f1s = list(f1(r['precision'], r['recall']) for r in results)
    averageF1Score = sum(f1s) / len(f1s)
    if averageF1Score > best[1]:
        best = index, averageF1Score
    if averageF1Score < worst[1]:
        worst = index, averageF1Score

    print('Sequence Index:', index, 'Score:', f'{averageF1Score:.2f}')

print(f'Sequence Index with highest average F1 score: Index {best[0]}, Score: {best[1]:.2f}')
print(f'Sequence Index with lowest average F1 score: Index {worst[0]}, Score: {worst[1]:.2f}')


# %%
# Load each sequence and convert to svg using Musescore
try:
    jobsPath = tempPath / 'jobs.json'
    os.makedirs(tempPath)
    if not os.path.exists(svgsPath):
        os.makedirs(svgsPath)
    jobs = []
    hymns = loadHymnAnnotations(DATASETS / 'hymns' / 'sequences.txt')

    # Create batch job file
    for index, hymn in hymns.items():
        filename = tempPath / f'hymn{index}.musicxml'
        hymn.write('musicxml', filename)
        job = {
            "in": filename.resolve().as_posix(),
            "out": (svgsPath / f'hymn{index}.svg').resolve().as_posix()
        }
        jobs.append(job)
    with open(jobsPath, 'w') as f:
        f.write(json.dumps(jobs))
    
    # Run musescore
    subprocess.run([MSCORE, '-j', jobsPath.resolve().as_posix()], shell=True)
finally:
    if os.path.exists(tempPath):
        shutil.rmtree(tempPath)

# %%
# Create ground truth images

if not os.path.exists(screenshotsPath):
    os.makedirs(screenshotsPath)

svgMarker = '@@@svg@@@'
annMarker = '@@@ann@@@'
with open(templatePath) as f:
    template = f.read() 
annotations = loadHymnAnnotations(DATASETS/'hymns'/'annotations.txt')
svgPaths = list(sorted(svgsPath.glob('*.svg')))
for svgPath in svgPaths:
    filename = svgPath.as_posix()
    index = int(re.search(r'hymn(\d+)-', filename).groups()[0])
    with open(svgPath) as f:
        svg = f.read()

    hymnPath = screenshotsPath / f'hymn{index}'
    if not os.path.exists(hymnPath):
        os.mkdir(hymnPath)

    # Insert svg into template
    templateWithSvg = template.replace(svgMarker, svg)

    # Create a separate image for each annotation of a hymn
    hymnAnnotations = annotations[index]
    for i, ann in enumerate(hymnAnnotations):

        # Format annotations
        formatted = formatAnnotation(((chr(65 + i), ann) for i, ann in enumerate(ann)))

        # Insert annotation into template
        newContent = templateWithSvg.replace(annMarker, '`' + formatted + '`')

        # Hydrate the template file
        if os.path.exists(tempPath):
            shutil.rmtree(tempPath)
        os.makedirs(tempPath)
        with open((tempPath / 'temp.html').as_posix(), 'w') as f:
            f.write(newContent)

        # Create the image file
        uri = (tempPath/'temp.html').resolve().as_uri()
        savePath = (hymnPath / f'ann{i + 1}.png').resolve().as_posix()
        args = fr'''"{str(CHROME)}" --headless --disable-gpu --screenshot="{str(savePath)}" --window-size=3500,3000 --hide-scrollbars "{uri}"'''
        subprocess.run(args, shell=True)   

        import Image
        image=Image.open('L_2d.png')

        imageBox = image.getbbox()
        cropped=image.crop(imageBox)
        cropped.save('L_2d_cropped.png') 

# %% [markdown]
# 


