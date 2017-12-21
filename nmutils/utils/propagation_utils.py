""" Isolated helper functions related to coherent wavefront propagation. """

import numpy as np

try:
    import pyfftw
except:
    pass

# at this point, with a 300x300 image, FFTW is about twice as fast as numpy. Threading doesn't help at this point. 
# FFTW can be improved using the pyfftw.FFTW class or the pyfftw.builders functions.
def fft(a):
    #a = np.fft.fftn(a)
    a = pyfftw.interfaces.numpy_fft.fftn(a, threads=1)
    a = np.fft.fftshift(a)
    return a
    
def ifft(a):
    a = np.fft.ifftshift(a)
    a = pyfftw.interfaces.numpy_fft.ifftn(a, threads=1)
    #a = np.fft.ifftn(a)
    return a

def propagateNearfield(A, psize, distances, energy):     

    """           
    Propagates the complex wavefront in N-by-N ndarray to the plane(s)
    specified as distances. The physical spacing of array elements is 
    psize, and the beam energy is specified in keV. An array 
    length(distances) x N x N is returned.

    The underlying code is ptypy's Geo class, which is essentially
    wrapped here.
    """

    import ptypy
    from distutils.version import LooseVersion
    if LooseVersion(ptypy.version) > LooseVersion('0.2.0.dev'):
        raise Exception('This script must be updated to work with ptypy > 0.2.0')

    # check for square matrix
    try:
        assert len(A.shape) == 2
        assert A.shape[0] == A.shape[1]
    except AssertionError:
        raise RuntimeError("Wavefront array must be N x N")

    # passing a single distance is allowed too
    try:
        len(distances)
    except TypeError:
        distances = [distances]

    # parameters for the propagator
    geo_pars = ptypy.core.geometry.DEFAULT.copy(depth=10)
    geo_pars.energy = energy
    geo_pars.distance = distances[0]
    geo_pars.resolution = psize
    geo_pars.psize = psize
    geo_pars.shape = A.shape[0]
    geo_pars.propagation = 'nearfield'

    # create the propagator
    geo = ptypy.core.geometry.Geo(pars=geo_pars)

    # prepare a 3D matrix for propagated wavefronts
    N = len(distances)
    result = np.zeros((N,) + A.shape, dtype=A.dtype)

    # iterate over the distances and propagate to there
    for i in range(N):
        geo.p.distance = distances[i]
        geo.update()
        result[i, :, :] = geo.propagator.fw(A)

    return result
