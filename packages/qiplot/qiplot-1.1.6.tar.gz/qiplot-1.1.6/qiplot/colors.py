import numpy as np
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap as LSC

global BASECM
BASECM = np.array([[0,255,255,255], [0, 0, 255, 255], [192,0,192,255], [255, 0, 0, 255], [255,255,0,255]])/255


def getcmcolors(length, cmapname):
    cmap_inds = np.linspace(5, 250, length).astype(np.uint8)
    try:
        cmapobj = getattr(cm, cmapname)
    except:
        color = BASECM
        cmapobj = LSC.from_list('default', color)
        #print('Using default colormap')
    return [tuple([int(255*j) for j in cmapobj(i)]) for i in cmap_inds]


