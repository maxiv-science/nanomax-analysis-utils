

################################################################################
#
#   imports and definition of global variables
#
################################################################################

from __future__         import division, print_function
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy            as np
import os
import readline
readline.set_completer_delims(' \t\n')              # allow for tab completion 
readline.parse_and_bind("tab: complete")            # of paths in raw_input
#from skimage.feature    import register_translation
from skimage.registration import phase_cross_correlation
from scipy.ndimage      import fourier_shift
import sys
import warnings
warnings.filterwarnings("ignore")                   # fixme: find a better way to stop warnings

global expected_keywords
expected_keywords = ['im1', 'im2', 'pxsize_nm', 'aligned', 'cropping']

################################################################################
#
#   2D case - Fourier Ring Correlation
#       https://en.wikipedia.org/wiki/Fourier_shell_correlation
#       http://www.sciencedirect.com/science/article/pii/S1047847713001184
#
################################################################################

def fourier_ring_correlation(im1, im2, binning=1.):    
    im1_fft = np.fft.fftshift(np.fft.fft2(im1))
    im2_fft = np.fft.fftshift(np.fft.fft2(im2))
    y, x    = np.indices((im1_fft.shape))    
    center  = [np.shape(im1_fft)[0]//2, np.shape(im1_fft)[1]//2]
    r       = np.sqrt(((x - center[1])/(1.*center[1]))**2 + ((y - center[0])/(1.*center[0]))**2)
    r       = r*0.5*np.max(im1_fft.shape)/binning
    r       = r.astype(int)

    a_real  = np.bincount(r.ravel(), np.real(im1_fft * np.conj(im2_fft)).ravel())
    a_imag  = np.bincount(r.ravel(), np.imag(im1_fft * np.conj(im2_fft)).ravel())
    b1      = np.bincount(r.ravel(), (np.abs(im1_fft)*np.abs(im1_fft)).ravel())
    b2      = np.bincount(r.ravel(), (np.abs(im2_fft)*np.abs(im2_fft)).ravel())

    nr      = np.bincount(r.ravel())                                    # number of pixels per shell
    frc     = (a_real+1j*a_imag)/np.sqrt(b1*b2)                         # actuall correlation of each shell
    x       = np.array(range(len(frc)))/(0.5*np.max(im1_fft.shape))     # spatial resolution / nyquist per shell
    x       = x*binning
    return np.abs(frc), nr, x

def crop_from_center2D(image, cropping):
    dy, dx  = cropping[0]//2, cropping[1]//2
    ly, lx  = np.shape(image)
    my, mx  = ly//2, lx//2
    return image[my-dy:my+dy, mx-dx:mx+dx]

def apply_window2D(image, type='hanning'):
    ly, lx  = np.shape(image)
    if      type=='hamming':    py, px = np.hamming(ly),    np.hamming(lx)
    elif    type=='bartlett':   py, px = np.bartlett(ly),   np.bartlett(lx)
    elif    type=='blackman':   py, px = np.blackman(ly),   np.blackman(lx)
    elif    type=='hanning':    py, px = np.hanning(ly),    np.hanning(lx)
    elif    type=='kaiser':     py, px = np.kaiser(ly),     np.kaiser(lx)
    half_y  = np.repeat(py, lx).reshape((ly,lx))
    half_x  = np.repeat(px, ly).reshape((lx,ly)).T
    return image*half_x*half_y

def remove_legendre(lines, deg=1):
    xval = np.array(range(len(lines[0])))
    yval = np.array(range(len(lines[0])))
    coef = np.polynomial.legendre.legfit(x=xval, y=lines.T, deg=deg)
    calc = np.polynomial.legendre.legval(x=yval, c=coef)
    return lines-calc

def align_images(im1, im2, cropping, N=10, precision=0.01, removelegendre=False):
    if len(cropping)==1:
        cropping    = [cropping, cropping]
    for i in range(N):
        #### cropping out the regions to align on
        im1_crop    = crop_from_center2D(im1, cropping).real
        im2_crop    = crop_from_center2D(im2, cropping).real
        if  removelegendre:
            ### removing legendre polynomy of the first oder... (phase wedge)
            im1_crop    = remove_legendre(im1_crop)
            im2_crop    = remove_legendre(im2_crop)
        ### measure the shift between the images and align the 2nd to the 1st image
        shift, error, diffphase = register_translation(im1_crop, im2_crop, 1./precision)
        im2 = np.fft.ifftn(fourier_shift(np.fft.fftn(im2), shift))
        print('    '+str(i+1)+'/'+str(N)+', '+str(shift))
    return im1.real, im2.real

################################################################################
#
#   3D case - Fourier Shell Correlation
#
################################################################################

def fourier_shell_correlation(vol1, vol2, binning=1.):    
    vol1_fft    = np.fft.fftshift(np.fft.fftn(vol1))
    vol2_fft    = np.fft.fftshift(np.fft.fftn(vol2))
    z, y, x     = np.indices((vol1_fft.shape))    
    center      = [np.shape(vol1_fft)[0]//2, np.shape(vol1_fft)[1]//2, np.shape(vol1_fft)[2]//2]
    r       = np.sqrt(((x - center[2])/(1.*center[2]))**2 + ((y - center[1])/(1.*center[1]))**2 + ((z - center[0])/(1.*center[0]))**2)
    r       = r*0.5*np.max(im1_fft.shape)/binning
    r       = r.astype(np.int)
    a_real  = np.bincount(r.ravel(), np.real(vol1_fft * np.conj(vol2_fft)).ravel())
    a_imag  = np.bincount(r.ravel(), np.imag(vol1_fft * np.conj(vol2_fft)).ravel())
    b1      = np.bincount(r.ravel(), (np.abs(vol1_fft)* np.abs(vol1_fft)).ravel())
    b2      = np.bincount(r.ravel(), (np.abs(vol2_fft)* np.abs(vol2_fft)).ravel())

    nr      = np.bincount(r.ravel())                                    # number of voxels per shell
    fsc     = (a_real+1j*a_imag)/np.sqrt(b1*b2)                         # actuall correlation of each shell
    x       = np.array(range(len(fsc)))/(0.5*np.max(im1_fft.shape))     # spatial resolution / nyquist per shell
    x       = x*binning
    return np.abs(fsc), nr, x

def crop_from_center3D(volume, cropping):
    dz, dy, dx  = cropping[0]//2, cropping[1]//2, cropping[2]//2
    lz, ly, lx  = np.shape(volume)
    mz, my, mx  = lz//2, ly//2, lx//2
    return volume[mz-dz:mz+dz, my-dy:my+dy, mx-dx:mx+dx]

def apply_window3D(volume, type='hanning'):     # fixme ... general version for every n-dimensional case
    lz, ly, lx  = np.shape(volume) 
    if      type=='hamming':    pz, py, px = np.hamming(lz),    np.hamming(ly),     np.hamming(lx)
    elif    type=='bartlett':   pz, py, px = np.bartlett(lz),   np.bartlett(ly),    np.bartlett(lx)
    elif    type=='blackman':   pz, py, px = np.blackman(lz),   np.blackman(ly),    np.blackman(lx)
    elif    type=='hanning':    pz, py, px = np.hanning(lz),    np.hanning(ly),     np.hanning(lx)
    elif    type=='kaiser':     pz, py, px = np.kaiser(lz),     np.kaiser(ly),      np.kaiser(lx)
    half_z  = np.repeat(pz, ly*lx).reshape((lz, ly, lx))
    half_y  = np.repeat(py, lz*lx).reshape((ly, lz, lx))
    half_y  = np.rollaxis(half_y, 1)
    half_x  = np.repeat(px, lz*ly).reshape((lx, ly, lz)).T
    return volume*half_x*half_y*half_z

# fixme -   So far no automated alignment functions for 3D because it's not needed
#           when two volumes are reconstructed from two halfs of the same 
#           tomographic data set.

################################################################################
#
#   Threshold Criteria
#       http://www.sciencedirect.com/science/article/pii/S1047847705001292
#
################################################################################

def frc_sigma_curve(sigma_factor, nr, n_asym=1.):
    result = sigma_factor*np.sqrt(n_asym)/np.sqrt(nr*0.5)
    result[nr==0]   = 1
    return result
    
def frc_one_bit_curve(nr):
    result = (0.5+2.4142/np.sqrt(nr))/(1.5+1.4142/np.sqrt(nr))
    result[nr==0]   = 1
    return result

def frc_one_bit_curve_freq(x_freq, cropping):
    result = (0.5+2.4142/np.sqrt(x_freq*np.min(cropping)*np.pi))/(1.5+1.4142/np.sqrt(x_freq*np.min(cropping)*np.pi))
    result[x_freq==0]   = 1
    return result

def frc_half_bit_curve(nr):
    result = (0.2071+1.9102/np.sqrt(nr))/(1.2071+0.9102/np.sqrt(nr))
    result[nr==0]   = 1
    return result

def frc_half_bit_curve_freq(x_freq, cropping):
    result = (0.2071+1.9102/np.sqrt(x_freq*np.min(cropping)*np.pi))/(1.2071+0.9102/np.sqrt(x_freq*np.max(cropping)*np.pi))
    result[x_freq==0]   = 1
    return result
################################################################################
#
#   Functions to evaluate the the calculated FSC or FRC
#
################################################################################

def spectral_snr(fourier_correlation, residuum=0.0):
    return 2*fourier_correlation[1:-1] / (1-fourier_correlation[1:-1] + residuum)

def list_func_index(lst, func):
    for i in range(len(lst)):
        if func(lst[i]):
            return i
      #raise ValueError('no element making func True')
    return len(lst)
def is_leq_zero(x):
    return x <= 0.

def find_x_cut(curve1, curve2, ignore_first=2):
    lmin        = np.min([len(curve1), len(curve2)])
    curve1      = curve1[:lmin]
    curve2      = curve2[:lmin]
    div         = (curve1/curve2)-1
    return list_func_index(div[ignore_first:], is_leq_zero)+ignore_first-1

def x_to_nm(px_nm, x):
    with warnings.catch_warnings():         # not printing warnings
        warnings.simplefilter("ignore")
        result = 1.*px_nm/x                 # fixme
    return result

def nm_to_x(px_nm, nm):
    return 1.*px_nm/nm 

def integrate_curve(points, function, low_limit=0, high_limit=1):
    low_index = points[points>=low_limit].argmin()
    high_index = points[points<=high_limit].argmax()
    if low_index==0:
        low_index += 1
    if high_index==(len(points)-1):
        high_index -= 1
    result = (function[low_index:high_index] + function[low_index+1:high_index+1])/2.
    result *= points[low_index+1:high_index+1] - points[low_index:high_index]
    result = np.sum(result)
    if (low_index>0) and (low_limit!=low_index):
        a,b = points[low_index-1], points[low_index]
        A,B = function[low_index-1], function[low_index]
        result += (A+B)*(b-low_limit)/2. + (B-A)*(low_limit-a)*(b-low_limit)/2./(b-a)
    if (high_index<(len(points)-1)) and (high_limit!=high_index):
        a,b = points[high_index], points[high_index+1]
        A,B = function[high_index], function[high_index+1]
        result += A*(high_limit-a) + (B-A)*(high_limit-a)**2/2./(b-a)
    return result



################################################################################
#
#   usage as a script
#
################################################################################

def print_n_exit(string):
    print(string)
    sys.exit()

def parse_args():
    kwargs  = dict(x.split('=', 1) for x in sys.argv[1:] if ('=' in x))
    args    = [x for x in sys.argv[1:] if not('=' in x)]
    return args, kwargs

def check_if_kwargs_in_args(args, kwargs):
    n   = len(args)
    for i, arg in enumerate(args):
        if arg in expected_keywords and i<=n-2:
            kwargs[arg] = args[i+1]
    return args, kwargs

def ask_for_keyword(keyword):
    if sys.version_info[0]==2:      input_str = raw_input('Please enter value for '+keyword+' : ')
    elif sys.version_info[0]==3:    input_str = input('Please enter value for '+keyword+' : ')
    if not check_input_str(keyword, input_str):
        input_str = ask_for_keyword(keyword)
    return input_str

def check_input_str(keyword, input_str):
    ### check if path to a file
    if keyword in ['im1', 'im2']:
        if not os.path.isfile(input_str):
            print('[ERROR] - value "'+path+'" for '+keyword+' is not a path to a file')
            return False
    ### check if boolean
    if keyword in ['aligned']:  
        if not input_str in ['True', 'False', '1', '0']:
            print('[ERROR] - value "'+input_str+'" for '+keyword+' is not a boolean expression')
            return False
    ### check if integer number
    if keyword in []: #['cropping']     #fixme: should be checked to be list of integer or intger
        if not input_str.isdigit():
            print('[ERROR] - value "'+input_str+'" for '+keyword+' is not an integer')
            return False
    ### check if float:
    if keyword in ['pxsize_nm']:
        try: a = float(input_str)
        except:
            print('[ERROR] - value "'+input_str+'" for '+keyword+' is not a float')
            return False
    return True

def read_image(fpath):
    if fpath.endswith('.edf') or fpath.endswith('.bin'):
        if sys.version_info[0]==3: print_n_exit("[ERROR] sadly i can't read edfs or bins from python3 (yet). Try python2!") #fixme
        try: from petrapy.fileio.edf import edf
        except: print_n_exit('[ERROR] could not load edf module\n-> exiting')
        try: image = edf.read(fpath)
        except: print_n_exit('[ERROR] could not load file '+fpath+'\n-> exiting')
        return image
    elif fpath.endswith('.tif') or fpath.endswith('.tiff'):
        try:
            with warnings.catch_warnings():         # not printing warnings
                warnings.simplefilter("ignore") 
                from petrapy.fileio.tiff import tiff
        except: print_n_exit('[ERROR] could not load tiff module\n-> exiting')
        try: image = tiff.read(fpath)
        except: print_n_exit('[ERROR] could not load file '+fpath+'\n-> exiting')
        return image
    else:
        print_n_exit("[ERROR] can't read file format of "+fpath+'\n-> exiting')

def main():
    global args, kwargs
    args, kwargs        = parse_args()
    args, kwargs        = check_if_kwargs_in_args(args, kwargs) 

    ### checking if the user typed in understandable keyword arguments
    given_keywords      = [keyword for keyword in kwargs if keyword in expected_keywords]
    for keyword in given_keywords:
        if not check_input_str(keyword, kwargs[keyword]):
            kwargs[keyword] = ask_for_keyword(keyword)

    ### checking if the user typed in all needed keywords
    missing_keywords    = [keyword for keyword in expected_keywords if keyword not in kwargs]
    if missing_keywords != []:
        print('Some keywords values are missing.')
        for keyword in missing_keywords:
                kwargs[keyword] = ask_for_keyword(keyword)

    ### reading all needed data
    im1         = read_image(kwargs['im1'])
    im2         = read_image(kwargs['im2'])
    aligned     = eval(kwargs['aligned'])
    cropping    = eval(kwargs['cropping'])
    pxsize_nm   = float(kwargs['pxsize_nm'])
    print('#'*80) 
    print('    given image #1:           '+kwargs['im1'])
    print('    given image #2:           '+kwargs['im2'])
    print('    given pixel size:         '+str(pxsize_nm)+' nm')
    print('    are they already aligned: '+str(aligned))
    print('    choosen cropping:         '+str(cropping))
    print('#'*80) 

    if len(cropping)==1:
        cropping    = (cropping, cropping)

    ### mirror one image if needed
    if 'mirror' in sys.argv:
        im2 = im2[:,::-1]
        print('    mirroring the 2nd image (symmetry axis is the vertical axis)')

    ### remove Legrende Polynomes of first order (phase wedge) for alignemnt
    removelegendre  = False
    if ('legendre_align' in sys.argv) or ('legendre' in sys.argv):
        removelegendre  = True
        print('    removing legendre polynomes (phase wedges)')

    ### aligning images if needed
    if not aligned: 
        print('    started alignment')
        im1, im2    = align_images(im1, im2, cropping, removelegendre=removelegendre)
        print('    finished alignment')
        print('#'*80) 

    ### cropping the aligned images
    crop1   = crop_from_center2D(im1, cropping)
    crop2   = crop_from_center2D(im2, cropping)

    ### remove Legrende Polynomes of first order (phase wedge) for calculation
    if ('legendre_calc' in sys.argv) or ('legendre' in sys.argv):
        crop1   = remove_legendre(crop1)
        crop2   = remove_legendre(crop2)

    ### plot the aligned images and their difference
    if ('plot' in args):
        fig     = plt.figure(figsize=(8,3), facecolor='white')
        plt.subplot(1,3,1)
        plt.imshow(crop1, interpolation='none')
        plt.title('image1')
        plt.subplot(1,3,2)
        plt.imshow(crop2, interpolation='none')
        plt.title('image2')
        plt.subplot(1,3,3)
        plt.imshow(crop1-crop2, interpolation='none')
        plt.title('difference')
        plt.tight_layout()

    # apply the window function
    crop1   = apply_window2D(crop1, type='hanning')
    crop2   = apply_window2D(crop2, type='hanning')

    ### calculating an printing the measured fourier ring correlation and ssnr
    print('   started calculation')
    fsc, nr, x  = fourier_ring_correlation(crop1, crop2)
    ssnr = spectral_snr(fsc)
    x_nm        = x_to_nm(x, pxsize_nm)

    ### smooth half/ and one bit curves                     ### correct, but spiky cruves
    y_half_bit  = frc_half_bit_curve_freq(x, cropping)      # frc_half_bit_curve(nr)
    y_one_bit   = frc_one_bit_curve_freq(x, cropping)       # frc_one_bit_curve(nr)
    x_half_bit  = x[find_x_cut(fsc, y_half_bit)]
    x_one_bit   = x[find_x_cut(fsc, y_one_bit)]
    nm_half_bit = x_to_nm(pxsize_nm, x_half_bit)
    nm_one_bit  = x_to_nm(pxsize_nm, x_one_bit)
    area = integrate_curve(x, fsc, 0.0, 1.0)

    ### plot the calculated results
    print('   finished calculation')
    print('#'*80) 
    print('    resolution: '+ str(nm_one_bit)[:5] +     ' nm (one bit criteria)')
    print('    resolution: '+ str(nm_half_bit)[:5] +    ' nm (half bit criteria)')
    print('     int. area: '+ str(area))
    print('#'*80) 

    if ('plot' in args) or ('save' in args):              
        ########################################################################
        #   plot the spectral signal to noise ratio and the reference
        ########################################################################
        fig1     = plt.figure(figsize=(9, 5), facecolor='white')
        ax1     = plt.subplot(1,1,1)

        line0,  = ax1.plot(x[1:-1], ssnr,          lw=2,           c='r',              label='ssnr')
        line4   = ax1.axhline(y=1,  lw=2, ls='--',  c='k', alpha=0.5,   label='SNR = 1')

        plt.xlim([0.0001, 1.])
        plt.ylim([0.05,1.05*ssnr.max()])
        plt.semilogy()
        plt.xlabel('spatial frequency / nyquist')
        plt.grid(which='both')
        plt.legend(loc=1)

        ########################################################################
        #   add a second axis with the resolution
        ########################################################################
        ax2         = ax1.twiny()

        xticks      = ax1.get_xticks()
        xtick_str   = ['']
        for xtick in xticks[1:]: 
            xtick_str.append(str(x_to_nm(pxsize_nm, xtick))[:6])
        plt.xticks(xticks, xtick_str)
        plt.xlabel('resolution in [nm]')
        plt.tight_layout()



        ########################################################################
        #   plot the fsc, the reference curves and their intersections
        ########################################################################
        fig2     = plt.figure(figsize=(12, 8), facecolor='white')
        ax2     = plt.subplot2grid((5, 1), (0, 0), rowspan=4)

        line0,  = ax2.plot(x, fsc,          lw=2,           c='r',              label='frc')
        line1,  = ax2.plot(x, y_half_bit,   lw=2, ls='-',   c='k', alpha=0.5,   label='_nolegend_')
        line2,  = ax2.plot(x, y_one_bit,    lw=2, ls='--',  c='k', alpha=0.5,   label='_nolegend_')
        line3   = ax2.axvline(x=x_half_bit, lw=2, ls='-',   c='k', alpha=0.5,   label='.5 bit criteria - '+str(nm_half_bit)[:5]+' nm')
        line4   = ax2.axvline(x=x_one_bit,  lw=2, ls='--',  c='k', alpha=0.5,   label='1 bit criteria - '+str(nm_one_bit)[:5]+' nm')

        plt.xlim([0.0001, 1.])
        plt.ylim([0,1.])
        plt.xlabel('spatial frequency / nyquist')
        plt.grid(which='both')
        plt.legend(loc=1)

        ########################################################################
        #   add a second axis with the resolution
        ########################################################################
        ax2         = ax2.twiny()

        xticks      = ax2.get_xticks()
        xtick_str   = ['']
        for xtick in xticks[1:]: 
            xtick_str.append(str(x_to_nm(pxsize_nm, xtick))[:6])
        plt.xticks(xticks, xtick_str)
        plt.xlabel('resolution in [nm]')

        ########################################################################
        ### 2nd plot with the details of how the script was called
        ########################################################################
        ax3     = plt.subplot2grid((5, 1), (4, 0))

        plt.axis('off')
        plt.xlim(0, 100)
        plt.ylim(0, 100)

        plt.text(0,100,     'area under curve: '+str(area))
        plt.text(0, 80,     'image1: '+kwargs['im1'])
        plt.text(0, 60,     'image2: '+kwargs['im2'])
        plt.text(0, 40,     'already aligned: '+str(aligned))
        plt.text(0, 20,     'choosen cropping: '+str(cropping))
        plt.text(0, 0,      'pixel size : '+str(pxsize_nm)+' nm')

        if 'mirror' in sys.argv:
            plt.text(40, 20,     'image was mirrored')
        if 'legendre' in sys.argv:
            plt.text(40, 40,     'legrendre polynomes (phase wedge) were removed - (alignemnt and calculation)')
        elif 'legendre_align' in sys.argv:
            plt.text(40, 40,     'legrendre polynomes (phase wedge) were removed - (only for the alignemnt)')
        elif 'legendre_calc' in sys.argv:
            plt.text(40, 40,     'legrendre polynomes (phase wedge) were removed - (only for the calculation)')

        ########################################################################
        ### finally show the figure
        ########################################################################
        plt.tight_layout()
        if 'save' in args: 
            base_im1    = kwargs['im1'][::-1].split('.',1)[1][::-1]
            plt.savefig(base_im1+'.png')
        if 'plot' in args: 
            plt.show()

################################################################################
#   check if run as a script
################################################################################
"""
    usage examples:
    python2 fsc.py im1 image1.edf im2 image2.edf pxsize_nm 6.5379 aligned False cropping 256 plot
    python tools/fsc.py im1 ../../../../Desktop/fsc_37_38/37_0200_object_phase.tif im2 ../../../../Desktop/fsc_37_38/38_0200_object_phase.tif aligned 0 pxsize_nm 9. cropping 300,600 plot
    python tools/fsc.py im1 /gpfs/p06/2017/data/11003747/processed/0003_Monolith_1_tomo/scan_00217/rec_res/1000_object_phase.tif im2 /gpfs/p06/2017/data/11003747/processed/0003_Monolith_1_tomo/scan_00319/rec_res/1000_object_phase.tif aligned 0 pxsize_nm 8.95451 cropping 300,300 plot save mirror
    python tools/fsc.py im1 /gpfs/p06/2017/data/11003747/processed/0003_Monolith_1_tomo/scan_00218/rec_res/1000_object_phase.tif im2 /gpfs/p06/2017/data/11003747/processed/0003_Monolith_1_tomo/scan_00318/rec_res/1000_object_phase.tif aligned 0 pxsize_nm 8.95451 cropping 300,560 plot save mirror legendre
"""
if __name__ == '__main__':
    main()
