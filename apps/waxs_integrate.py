"""
Script which radially integrates the 2D data contained in a hdf5 file
or list of files.

This is still python 2! Waiting for pyfai installation.
"""

import pyFAI, fabio
import h5py
import numpy as np
import os, time, sys, argparse

### Parse input
parser = argparse.ArgumentParser(
    description='This script integrates all detector frames in a hdf5 file or list of files.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('poni_file', type=str,
                    help='The pyFAI calibration file. Determines what data to take from the input file.')
parser.add_argument('input_files', type=str, nargs='*',
                    help='The file(s) containing the input data. They all have to be in the same folder unless an absolute output path is given.')
parser.add_argument('--mask_file', type=str, dest='mask_file',
                    help='Mask file, edf format from pyFAI.')
parser.add_argument('--output_folder', type=str, dest='output_folder', default=None,
                    help='Output folder. If relative, it refers to the input folder. By default uses the an analog of the input folder under ../../process/radial_integration/<sample name>.')
parser.add_argument('--nbins', type=int, dest='nbins', default=2000,
                    help='Number of q bins.')
args = parser.parse_args()


### work out where the input folder is and if it is unique if needs be
if (not args.output_folder) or (not args.output_folder[0] == '/'):
    input_folders = [os.path.dirname(f) for f in args.input_files]
    input_folders = list(set(input_folders))
    if not len(input_folders) == 1:
        raise InputError('Since the files are in different places, you have to specify an absolute output folder.')
    input_folder = input_folders[0]

### work out where to put the data
if not args.output_folder:
    output_folder = os.path.join(input_folder.split('/raw/')[0],
                                 'process/radial_integration',
                                 os.path.basename(os.path.abspath(input_folder)))
elif args.output_folder[0] == '/':
    # absolute path
    output_folder = args.output_folder
else:
    # relative path
    output_folder = os.path.abspath(os.path.join(input_folder, args.output_folder))


### define some helper functions
def dict_walk(dct, ignore=[]):
    """
    Recursively walks through a dict, returning each non-dict value.
    """
    if str(ignore) == ignore:
        ignore = [ignore,]
    for k, v in dct.items():
        if hasattr(v, 'iteritems'):
            if v.name.split('/')[-1] in ignore:
                continue
            for v_ in dict_walk(v, ignore=ignore):
                yield v_
        else:
            yield v

def images(fp, shape=None, ignore=[]):
    """
    Iterates over the 2D images, optionally of a certain shape, of
    an hdf5 file.
    """
    for v in dict_walk(fp, ignore=ignore):
        if len(v.shape) >= 2 and (shape is None or v.shape[-2:] == shape):
            # make an array (n, M, N) where n is the number of images
            arr = np.reshape(v, (-1,)+v.shape[-2:])
            for im in arr:
                yield im


### Do the work
integrator = pyFAI.load(args.poni_file)
for input_file in args.input_files:
    inputfn = os.path.basename(input_file)
    print '*** Integrating %s' % inputfn
    outputfn = inputfn.split('.')[0] + '_waxs.' + inputfn.split('.')[-1]
    output_file = os.path.join(output_folder, outputfn)
    assert '/raw/' not in output_file

    if not os.path.exists(os.path.dirname(output_file)):
        print '****** Creating directory %s' % os.path.dirname(output_file)
        os.makedirs(os.path.dirname(output_file))

    if args.mask_file:
        mask = fabio.open(args.mask_file).data
    else:
        mask = None

    intensities = []
    with h5py.File(input_file, 'r') as fpin:    
        for im in images(fpin, ignore='instrument'):
            if not im.shape == integrator.get_shape():
                print('skipping data %s' % (str(im.shape)))
                continue
            out = integrator.integrate1d(data=im, npt=args.nbins, filename=None, mask=mask)
            q, I = out.radial, out.intensity
            intensities.append(I)
        I = np.array(intensities)
    with h5py.File(output_file, 'w') as fpout:
        fpout['I'] = I
        fpout['q'] = q

