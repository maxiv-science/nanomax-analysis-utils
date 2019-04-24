"""
Script which radially integrates the data in a specific folder,
watching for new data as it appears.

DRAFT
"""

import pyFAI, fabio
import h5py
import numpy as np
import os, time, sys

def dict_walk(dct, ignore=[]):
    """
    Recursively walks through a dict, returning each non-dict value.
    """
    if str(ignore) == ignore:
        ignore = [ignore,]
    for k, v in dct.iteritems():
        if hasattr(v, 'iteritems'):
            if v.name.split('/')[-1] in ignore:
                continue
            for v_ in dict_walk(v, ignore=ignore):
                yield v_
        else:
            yield v

def count_images(fp, shape=None, ignore=[]):
    """
    Counts the number of 2D images, optionally of a certain shape,
    in an hdf5 file.
    """
    counts = 0
    for v in dict_walk(fp, ignore=ignore):
        if len(v.shape) >= 2 and (shape is None or v.shape[-2:] == shape):
            counts += np.prod(v.shape) / np.prod(v.shape[-2:])
    return counts


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

def integrate_file(input_file, output_file):
    """
    Does the actual integration and file saving.
    """

    integrator = pyFAI.load(PONI_FILE)
    mask = fabio.open(MASK_FILE).data
    intensities = []

    with h5py.File(input_file, 'r') as fpin:    
        N = count_images(fpin, ignore='instrument')
        n = 1
        fmt = '\r%%0%uu / %%u' % int(np.ceil(np.log10(N)))
        for im in images(fpin, ignore='instrument'):
            if n % 10 == 0:
                sys.stdout.write(fmt % (n, N))
                sys.stdout.flush()
            out = integrator.integrate1d(data=im, npt=NBINS, filename=None, mask=mask)
            q, I = out.radial, out.intensity
            intensities.append(I)
            n += 1
        print ''
        I = np.array(intensities)
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    with h5py.File(output_file, 'w') as fpout:
        meta = integrator.make_headers('dict')
        fpout['I'] = I
        fpout['q'] = q

# parameters to handle
PONI_FILE = '/home/alex/tmp/waxs/si_calib.poni'
MASK_FILE = '/home/alex/tmp/waxs/si_mask.edf'
INPUT_FOLDER = '/data/visitors/nanomax/20190570/2019041008/raw/as_deposited/'
OUTPUT_FOLDER = os.path.join(INPUT_FOLDER.split('/raw/')[0],
                             'process/radial_integration',
                             os.path.basename(os.path.dirname(INPUT_FOLDER)))
NBINS = 1000

for inputfn in os.listdir(INPUT_FOLDER):
    outputfn = inputfn.split('.')[0] + '_waxs.' + inputfn.split('.')[-1]
    output_file = os.path.join(OUTPUT_FOLDER, outputfn)
    input_file = os.path.join(INPUT_FOLDER, inputfn)
    if os.path.exists(output_file):
        with h5py.File(input_file, 'r') as fp:
            n_in = count_images(fp, ignore='instrument')
        with h5py.File(output_file, 'r') as fp:
            n_out = fp['I'].shape[0]
        if n_in == 0:
            print 'no images, skipping:\n', input_file
        elif n_in > n_out:
            print 'too few images in output file (%u, %u), integrating again:\n' % (n_in, n_out), input_file
            integrate_file(input_file, output_file)
        else:
            print 'already integrated:\n', input_file
    else:
        print 'output file doesn''t exist, integrating:\n', input_file
        integrate_file(input_file, output_file)
    time.sleep(1)
