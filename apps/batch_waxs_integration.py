"""
Script which radially integrates the data in a specific folder,
watching for new data as it appears.
"""

import pyFAI, fabio
import h5py
import numpy as np
import os, time, sys, argparse

FORCE, CHECK, REMEMBER = (0, 1, 2)

### Parse input
parser = argparse.ArgumentParser(
    description='This script integrates all detector frames in a folder.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('input_folder', type=str,
                    help='The folder containing the input data.')
parser.add_argument('poni_file', type=str,
                    help='The pyFAI calibration file.')
parser.add_argument('--mask_file', type=str, dest='mask_file',
                    help='Mask file, edf format from pyFAI.')
parser.add_argument('--output_folder', type=str, dest='output_folder', default=None,
                    help='Output folder. If relative, it refers to input_folder. By default uses the an analog of the input_folder under ../../process/radial_integration/<sample name>.')
parser.add_argument('--nbins', type=int, dest='nbins', default=500,
                    help='Number of q bins.')
parser.add_argument('--laziness', type=int, dest='laziness', default=2,
                    help='How lazy to be. You can (0) force integration once of all the files in the input folder, or (1) go over them repeatedly checking each time if the input files has more images than the output file, or (2) repeatedly go over the files but remember if files seem to be done.')
args = parser.parse_args()

### work out where to put the data
if not args.output_folder:
    output_folder = os.path.join(args.input_folder.split('/raw/')[0],
                                 'process/radial_integration',
                                 os.path.basename(os.path.abspath(args.input_folder)))
elif args.output_folder[0] == '/':
    # absolute path
    output_folder = args.output_folder
else:
    # relative path
    output_folder = os.path.abspath(os.path.join(args.input_folder, args.output_folder))

### define some helper functions
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

### do the actual loop. super messy, sorry about this...
done_lst = [] # list of remembered input files considered done
bad_list = [] # list of input files which haven't worked
while not args.laziness == FORCE:
    for inputfn in os.listdir(args.input_folder):
        time.sleep(1)
        print ''

        do_integ = False
        if not inputfn.endswith('.hdf5'):
            continue
        outputfn = inputfn.split('.')[0] + '_waxs.' + inputfn.split('.')[-1]
        output_file = os.path.join(output_folder, outputfn)
        assert '/raw/' not in output_file
        input_file = os.path.join(args.input_folder, inputfn)

        if input_file in bad_list:
            continue

        if args.laziness == FORCE or not os.path.exists(output_file):
            print 'integrating:\n', input_file
            do_integ = True
        else:
            if args.laziness == REMEMBER and input_file in done_lst:
                print 'skipping recognized file:\n', input_file
                continue
            with h5py.File(input_file, 'r') as fp:
                n_in = count_images(fp, ignore='instrument')
            with h5py.File(output_file, 'r') as fp:
                n_out = fp['I'].shape[0]
            if n_in > n_out:
                print 'too few images in output file (%u, %u), integrating again:\n' % (n_in, n_out), input_file
                do_integ = True
            elif args.laziness == CHECK:
                print 'no new data to integrate just now:\n', input_file
            else:
                done_lst.append(input_file)
                print 'no new data to integrate, remembering:\n', input_file

        if do_integ:
            integrator = pyFAI.load(args.poni_file)
            if args.mask_file:
                mask = fabio.open(args.mask_file).data
            else:
                mask = None
            intensities = []
            print output_file

            with h5py.File(input_file, 'r') as fpin:    
                N = count_images(fpin, ignore='instrument')
                n = 1
                fmt = '\r%%0%uu / %%u' % int(np.ceil(np.log10(N)))
                for im in images(fpin, ignore='instrument'):
                    if not im.shape == integrator.get_shape():
                        print 'data doesn''t match poni file, skipping and remembering.'
                        bad_list.append(input_file)
                        break
                    if n % 10 == 0:
                        sys.stdout.write(fmt % (n, N))
                        sys.stdout.flush()
                    out = integrator.integrate1d(data=im, npt=args.nbins, filename=None, mask=mask)
                    q, I = out.radial, out.intensity
                    intensities.append(I)
                    n += 1
                I = np.array(intensities)
            if len(intensities):
                if not os.path.exists(os.path.dirname(output_file)):
                    os.makedirs(os.path.dirname(output_file))
                with h5py.File(output_file, 'w') as fpout:
                    meta = integrator.make_headers('dict')
                    fpout['I'] = I
                    fpout['q'] = q
