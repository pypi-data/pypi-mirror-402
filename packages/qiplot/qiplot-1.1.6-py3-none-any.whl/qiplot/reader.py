import sys, os, re, string
import numpy as np
from glob import glob
import traceback
import logging
from logging.config import fileConfig

dname = glob(os.path.dirname(__file__))[0]
cfgname = dname + '/logconf.py'
fileConfig(cfgname)


class colfile:
    def __init__(self, x, y, e, arr):
        self.x = x
        self.y = y
        self.e = e
        self.arr = arr


def fromstring(s):
    ## check for letters other than e/E
    abpattern = '[a-df-zA-DF-Z:;=]+'
    if len(re.findall(abpattern, s)) > 0:
        return s, 0
    ## check for numbers including scientific notation
    numpattern = '[+\-]?[^A-Za-z]?(?:[0-9]\d*)?(?:\.\d*)?(?:[eE][+\-]?\d+)?'
    pts = re.findall(numpattern, s)
    out = []
    ## return the floats and skip empty lines
    for i in pts:
        try:
            val = float(i)
            out.append(val)
        except ValueError:
            pass
    if len(out) > 0:
        logging.debug('%s ok' %s)
        return out, 1
    else:
        logging.debug('%s fail' %s)
        return s, 0


def is_column_usable(column_data, nan_threshold=0.8):
    """
    Check if a column is usable (not mostly NaN or inf values)
    
    Args:
        column_data: numpy array of column values
        nan_threshold: fraction of NaN/inf values above which column is considered unusable
    
    Returns:
        bool: True if column is usable, False otherwise
    """
    if len(column_data) == 0:
        return False
    
    # Count NaN and inf values
    invalid_count = np.sum(~np.isfinite(column_data))
    invalid_fraction = invalid_count / len(column_data)
    
    # Column is usable if less than threshold fraction is invalid
    is_usable = invalid_fraction < nan_threshold
    
    if not is_usable:
        logging.debug(f'Column rejected: {invalid_fraction:.2%} invalid values (threshold: {nan_threshold:.2%})')
    
    return is_usable


def clean_column_data(column_data):
    """
    Clean column data by replacing NaN/inf with interpolated or zero values
    
    Args:
        column_data: numpy array to clean
        
    Returns:
        numpy array: cleaned data
    """
    if len(column_data) == 0:
        return column_data
    
    # Make a copy to avoid modifying original
    cleaned = column_data.copy()
    
    # Find finite values
    finite_mask = np.isfinite(cleaned)
    
    if not np.any(finite_mask):
        # All values are invalid, return zeros
        return np.zeros_like(cleaned)
    
    if not np.all(finite_mask):
        # Some values are invalid, try to interpolate or fill with zeros
        invalid_indices = np.where(~finite_mask)[0]
        
        # For error columns, replace invalid values with zero
        # For x,y columns, try linear interpolation if possible
        if np.sum(finite_mask) >= 2:
            # Enough finite values for interpolation
            finite_indices = np.where(finite_mask)[0]
            try:
                cleaned[invalid_indices] = np.interp(invalid_indices, finite_indices, cleaned[finite_indices])
            except:
                # Interpolation failed, use zeros
                cleaned[invalid_indices] = 0.0
        else:
            # Not enough finite values, use zeros
            cleaned[invalid_indices] = 0.0
    
    return cleaned


def linecheck(fname, maxbytes=-1):
    """
    Separates header lines from data lines
    """
    datalines = []
    headerlines = []
    with open(fname, 'r') as f:
        lines = [l.strip() for l in f.readlines(maxbytes)]
    for n, line in enumerate(lines):
        cols, numeric = fromstring(line)
        logging.debug('(%-3d %-5s) %s', n, bool(numeric), cols)
        if numeric == 1:
            datalines.append(cols)
        else:
            headerlines.append(f'{n}: {line}')
    logging.debug('end of loop')
    
    ### find ncols - be more flexible about column count
    if not datalines:
        logging.warning('No data lines found')
        return datalines, headerlines
    
    # Count occurrences of different column counts
    col_counts = {}
    for line in datalines:
        ncol = len(line)
        if ncol >= 2:  # Only consider lines with at least 2 columns
            col_counts[ncol] = col_counts.get(ncol, 0) + 1
    
    if not col_counts:
        logging.warning('No lines with at least 2 columns found')
        return [], headerlines
    
    # Use the most common column count (with at least 2 columns)
    target_ncols = max(col_counts.keys(), key=col_counts.get)
    datalines = [line for line in datalines if len(line) == target_ncols]
    
    logging.debug('Accepted %d lines out of %d with %d columns', 
                  len(datalines), len(lines), target_ncols)
    return datalines, headerlines


def fromcols(fname, usecols=None, maxbytes=-1):
    """
    Assign columns to values read from lines using linecheck()
    """
    data, header = linecheck(fname, maxbytes)
    
    if not data:
        # Return empty data if no valid data found
        logging.warning('No valid data found in file')
        empty_array = np.array([]).reshape(0, 0)
        return data, header, colfile(np.array([]), np.array([]), np.array([]), empty_array)
    
    dar = np.array(data).T
    logging.debug(f'data array shape: {dar.shape}')
    
    ### find X, Y, E columns
    if usecols is None:
        logging.debug('Argument --usecols not specified. Using default columns x=0, y=1')
        
        # Default: use first two columns (0, 1)
        if dar.shape[0] >= 2:
            x = clean_column_data(dar[0])
            y = clean_column_data(dar[1])
            
            # Check if there's a usable third column for errors
            if dar.shape[0] >= 3 and is_column_usable(dar[2]):
                e = clean_column_data(dar[2])
                logging.debug('Found usable third column for errors')
            else:
                e = np.zeros(y.shape)
                if dar.shape[0] >= 3:
                    logging.debug('Third column exists but contains too many invalid values, using zeros for errors')
                else:
                    logging.debug('No third column found, using zeros for errors')
        else:
            logging.error('File must have at least 2 columns')
            raise ValueError('File must have at least 2 columns')
            
    elif len(usecols) == 2:
        try:
            x = clean_column_data(dar[usecols[0]])
            y = clean_column_data(dar[usecols[1]])
            e = np.zeros(y.shape)
            logging.debug('Using 2 specified columns: x=%d, y=%d', usecols[0], usecols[1])
        except IndexError:
            logging.error('Specified columns not found in data')
            raise ValueError(f'Specified columns {usecols} not found in data with {dar.shape[0]} columns')
            
    elif len(usecols) == 3:
        try:
            x = clean_column_data(dar[usecols[0]])
            y = clean_column_data(dar[usecols[1]])
            
            # Check if the specified error column is usable
            if is_column_usable(dar[usecols[2]]):
                e = clean_column_data(dar[usecols[2]])
                logging.debug('Using 3 specified columns: x=%d, y=%d, e=%d', usecols[0], usecols[1], usecols[2])
            else:
                e = np.zeros(y.shape)
                logging.debug('Specified error column %d contains too many invalid values, using zeros', usecols[2])
                
        except IndexError:
            logging.error('Specified columns not found in data')
            raise ValueError(f'Specified columns {usecols} not found in data with {dar.shape[0]} columns')
        except Exception as err:
            logging.error('Error processing specified columns: %s', err)
            logging.error(traceback.format_exc())
            e = np.zeros(y.shape)
            
    else:
        logging.error('usecols must specify 2 or 3 columns')
        raise ValueError('usecols must specify 2 or 3 columns')
    
    return data, header, colfile(x, y, e, dar)


def get_xye(argfiles, usecols, maxbytes, label):
    argfiles = [glob(f'{arg}') for arg in argfiles]
    argfiles = sorted(set([j for i in argfiles for j in i]))
    names, data = [], []
    for ind, f in enumerate(argfiles):
        print(f'{ind:<4d}. {f}', end=': ')
        if os.path.isfile(f) is False:
            print('no file')
        else:
            try:
                cf = fromcols(f, usecols, maxbytes)[-1]
                print(f'{len(cf.x)} points')
                data.append([cf.x, cf.y, cf.e])
                if '/' in f:
                    sep = '/'
                elif '\\' in f:
                    sep = '\\'
                else:
                    sep = '\\'
                if label == 'index':
                    names.append(f.split(sep)[-1].split('.')[0].split('_')[-1])
                elif label == 'prefix':
                    names.append(f.split(sep)[-1].split('.')[0])
                elif label == 'dir':
                    names.append('/'.join(os.path.abspath(f).split(sep)[-2:]).split('.')[0])
                elif label == 'full':
                    names.append(os.path.abspath(f))
            except Exception as err:
                print('ERROR:', str(err))
                logging.error('Error processing file %s: %s', f, err)
                logging.error(traceback.format_exc())
                continue
    return data, names
