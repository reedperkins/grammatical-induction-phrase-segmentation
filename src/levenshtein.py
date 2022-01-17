import numpy as np


inf = float('inf')
def bandedEditDistance(a, b, sub, indel, width):
    if abs(len(a) - len(b)) > width // 2:
        return max(len(a), len(b))
    a, b = (b, a) if len(a) > len(b) else (a, b)
    rows, cols = len(a) + 1, len(b) + 1
    mtx = {}

    mtx[0, 0] = 0

    for i in range(1, rows):
        mtx[i, 0] = i * indel
    
    for j in range(1, width+1):
        mtx[0, j] = j * indel

    for i in range(1, rows):
        colRange = max(1, i - width // 2), min((i + width // 2) + 1, cols)
        for j in range(*colRange):
            mtx[i, j] = min(
                mtx.get((i-1, j), inf)   + indel,
                mtx.get((i, j-1), inf)   + indel,
                mtx.get((i-1, j-1), inf) + sub(a[i-1], b[j-1])
            )
            
    return mtx[rows-1, cols-1]

def bandedSimilarity(a, b, sub):
    d = bandedEditDistance(a, b, sub, indel=1, width=11)
    return 1 - (d / max(len(a), len(b)))

def dictToMtx(d, r, c):
    mtx = np.zeros((r, c))
    for (r, c), v in d.items():
        mtx[r, c] = v
    return mtx
    
def editDistance(a, b, sub, indel):
    rows, cols = len(a) + 1, len(b) + 1
    mtx = np.zeros((rows, cols))

    for i in range(1, rows):
        mtx[i, 0] = i * indel

    for j in range(1, cols):
        mtx[0, j] = j * indel 

    for i in range(1, rows):
        for j in range(1, cols):
            mtx[i, j] = min(
                mtx[i-1, j]   + indel,
                mtx[i,   j-1] + indel,
                mtx[i-1, j-1] + sub(a[i-1], b[j-1])
            )
    
    return mtx[-1, -1]

def similarity(a, b, sub, indel=1):
    d = editDistance(a, b, sub, indel)
    return 1 - (d / max(len(a) * indel, len(b) * indel))