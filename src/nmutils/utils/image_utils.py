""" Isolated helper functions for image array manipulation. """

import numpy as np
from numpy.lib.stride_tricks import as_strided
import scipy.signal
import scipy.ndimage
import math

def poisson(mean, k):
    """ Returns the normalized Poisson probability for observing k counts in a distribution described by the mean. """
    if type(k) in [list, tuple, np.ndarray]:
        result = []
        for k_ in k:
            result.append(mean**k_ * np.exp(-mean) / math.factorial(k_))
        return np.array(result)
    else:
        return mean**k * np.exp(-mean) / math.factorial(k)
    
def smoothImage(image, sigma):
    """ Returns a smoothened copy of the input image, which is convolved by a gaussian of standard deviation sigma. """
    size = max(3, 3 * int(round(sigma)))
    gaussian = gaussian2D(size, sigma)
    # fftconvolve() is faster than convolve2d (tested)
    # a copy of the image is created (also tested)
    smoothImage = scipy.signal.fftconvolve(image, gaussian, mode='same')
    return smoothImage
    
def noisyImage(image, photonsPerPixel=None, photonsAtMax=None, photonsTotal=None, dtype=None):
    """ 
    Returns a noisy copy of the input image, with simulated 
    photon-counting noise (Poisson noise) corresponding to:
    - an overall average number of photons per pixel, or
    - a certain number of photons expected in the maximum pixel, or
    - a certain number of total expected photons.
    
    You can specify the dtype of the output, by default it is the same 
    as the input image.
    """

    if not dtype:
        dtype = image.dtype

    if photonsPerPixel and not photonsAtMax and not photonsTotal:
        photonsTotal = np.prod(image.shape) * photonsPerPixel
    elif photonsAtMax and not photonsPerPixel and not photonsTotal:
        photonsTotal = np.sum(image) / np.max(image) * photonsAtMax
    elif photonsTotal and not photonsAtMax and not photonsPerPixel:
        pass
    else:
        raise ValueError('Confusing input to noisyImage')

    result = np.zeros(image.shape, dtype=dtype)
    totalSum = image.sum()
    if len(image.shape) == 2:
        for i in range(result.shape[0]):
            for j in range(result.shape[1]):
                expected = image[i, j] / totalSum * photonsTotal
                result[i, j] = np.random.poisson(expected)
    if len(image.shape) == 3:
        for i in range(result.shape[0]):
            for j in range(result.shape[1]):
                for k in range(result.shape[2]):
                    expected = image[i, j, k] / totalSum * photonsTotal
                    result[i, j, k] = np.random.poisson(expected)
    return result

def biggestBlob(image):
    """ Takes an image and returns a version with only the biggest continuous blob of non-zero elements left. """
    labeledImage, N = scipy.ndimage.label(image)
    # first, work out which is the biggest blob (except the background)
    areas = []
    for i in range(1, N + 1): # N doesn't include the background
        areas.append(sum(sum(labeledImage == i)))
    biggest = np.where(areas == max(areas))[0] + 1
    return (labeledImage == biggest)

def binPixels(image, n=2):
    """ Explicitly downsamples an image by an integer amount, by binning adjacent pixels n-by-n. Odd pixels on the bottom and right are discarded. """
    size = np.array(image.shape)
    size[0] = size[0] // n
    size[1] = size[1] // n
    new = np.zeros(size, dtype=image.dtype)
    for i in range(size[0]):
        for j in range(size[1]):
            tmp = np.mean(image[i * n : (i + 1) * n, j * n : (j + 1) * n], axis=(0, 1))
            if issubclass(image.dtype.type, np.integer):
                new[i, j] = np.round(tmp)
            else:
                new[i, j] = tmp
    return new

def fastBinPixels(image, n=2):
    """ Downsamples an image by stride-tricks downsampling. """
    strided = as_strided(image,
                shape=(image.shape[0]//n, image.shape[1]//n, n, n),
                strides=((image.strides[0]*n, image.strides[1]*n)+image.strides))
    return strided.sum(axis=-1).sum(axis=-1)

def gaussian2D(n, sigma):
    """ Returns an n-by-n matrix containing a circular 2d gaussian with variance sigma**2 in pixels. """
    mat = np.zeros((n, n))
    mu = (n - 1) / 2.0
    twoSigma2 = float(2 * sigma**2)
    prefactor = 1 / (twoSigma2 * np.pi)
    for i in range(n):
        for j in range(n):
            mat[i, j] = prefactor * np.exp(- ((i - mu)**2 + (j - mu)**2) / twoSigma2 )
            # the convolution darkens the image, not sure why, but this happens both with the scipy methods and
            # with a slow manual doulbe loop convolution... this number was obtained from a numerical test.
            mat[i, j] *= 100.0 / 77.9484
    return mat
    
def circle(n, radius=None, dtype='float'):
    """ Returns an n-by-n array of zeros with a filled circle of ones in its center, with default radius n/2. """
    result = np.zeros((n,n), dtype=dtype)
    if not radius:
        radius = n / 2.0
    I, J = result.shape
    for i in range(I):
        for j in range(J):
            result[i, j] = int((i-(I-1)/2.0)**2 + (j-(J-1)/2.0)**2 < radius**2)
    return result
    
def pseudoCircle(n, radius=None, exponent=1.5, dtype='float'):
    """ Returns an n-by-n array of zeros with a filled psuedo-circle of ones in its center, with default radius n/2. For exponent=1 this is a rhomb, for exponent=2 a circle, for high exponents a rounded-corner square."""
    result = np.zeros((n,n), dtype=dtype)
    if not radius:
        radius = n / 2.0
    I, J = result.shape
    for i in range(I):
        for j in range(J):
            result[i, j] = int(  np.abs(i-(I-1)/2.0)**exponent + np.abs((j-(J-1)/2.0))**exponent < radius**exponent ) 
    return result
