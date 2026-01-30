import os
import argparse



def parse_1d_arguments():
    parser = argparse.ArgumentParser(description='Lightweight, file-based plotting for Linux and Windows')
    parser.add_argument('datafiles', nargs='+', type=str,
                        help='String(s) passed to glob to look for plottable files')
    parser.add_argument('-l','--label', choices=['index','prefix','dir','full'],
                        default='prefix', help='Cut legend label at: \
                        index (0002), prefix (Cr2O3_98keV_x1200_0002), dir (Cr2O3/Cr2O3_98keV_x1200_0002),\
                        full (/data/id15/inhouse3/2018/ch5514/Cr2O3/Cr2O3_98keV_x1200_0002)')
    parser.add_argument('-t','--title', default=os.path.realpath('.').split('/')[-1], help='Window title')
    parser.add_argument('-o', '--offset', default=0, nargs='?', type=float,
                        help='Offset every successive curve by an arbitrary value. Default: 0')
    parser.add_argument('--every', default=1, type=int, help='Plot only every N-th input file')
    parser.add_argument('--diff', default=None, type=int, const=0, nargs='?',
                        help='If True, plot the difference between each curve and the N-th input curve. \
                              Default (no value) = 0 (first curve). To subtract mean use --diff -99. \
                              Error is propagated over the two curves.')
    parser.add_argument('--usecols', default=None, type=int, nargs='*',
                        help='List of columns to extract from each input file, to be provided as --usecols 0 2 3 \n\
                              Default: [0,1,2], meaning x=0, y=1, e=2. \
                              If no error column is found, the reader switches automatically to [0,1]. \
                              In general, this is useful only when x is not the first column.')
    parser.add_argument('--linewidth', default=1.25, type=float, nargs='?',
                        help='Width of plot lines. Default: 1.25')
    parser.add_argument('--maxbytes', type=int, nargs='?', default=-1,
                        help='Maximum size (in kB) to read from each file. This is useful when trying to read long files.')
    parser.add_argument('--cmap', type=str, default='spectral', nargs='?', help='One of the available matplotlib cmaps')
    parser.add_argument('--winsize', type=int, nargs=2, default=(1920,1080), help='Plot window size in pixels as width and height. Default: 1024 768')
    return parser.parse_args()




def parse_2d_arguments():
    parser = argparse.ArgumentParser(description='At least better than plotdata')
    parser.add_argument('datafiles', nargs='+', type=str,
                        help='String(s) passed to glob to look for plottable files')
    parser.add_argument('-l','--label', choices=['index','prefix','dir','full'],
                        default='prefix', help='Cut legend label at: \
                        index (0002), prefix (Cr2O3_98keV_x1200_0002), dir (Cr2O3/Cr2O3_98keV_x1200_0002),\
                        full (/data/id15/inhouse3/2018/ch5514/Cr2O3/Cr2O3_98keV_x1200_0002)')
    parser.add_argument('-t','--title', default=os.path.realpath('.').split('/')[-1], help='Window title')
    parser.add_argument('--every', default=1, type=int, help='Plot only every N-th input file')
    parser.add_argument('--diff', default=None, type=int, const=0, nargs='?',
                        help='If True, plot the difference between each curve and the N-th input curve. \
                              Default (no value) = 0 (first curve). To subtract mean use --diff -99. \
                              Error is propagated over the two curves.')
    parser.add_argument('--maxbytes', type=int, nargs='?', default=-1,
                        help='Maximum size (in kB) to read from each file. This is useful when trying to read long files.')
#    parser.add_argument('--cmap', type=str, default='viridis', nargs='?', help='One of the available matplotlib cmaps')
    parser.add_argument('--winsize', type=int, nargs=2, default=(1920,1080), help='Plot window size in pixels as width and height. Default: 1024 768')
    return parser.parse_args()