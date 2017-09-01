""" Isolated helper functions for array operations. """

import numpy as np
from scipy.ndimage import map_coordinates

def shift(a, shifts):
    """ Shifts an array periodically. """
    a_ = np.copy(a)
    shifts = map(int, shifts)
    # shift the first index: turns out to work with negative shifts too
    if shifts[0]:
        a_[shifts[0]:, :] = a[:-shifts[0], :]
        a_[:shifts[0], :] = a[-shifts[0]:, :]
        a = np.copy(a_)
    # shift the second index: same here
    if shifts[1]:
        a_[:, shifts[1]:] = a[:, :-shifts[1]]
        a_[:, :shifts[1]] = a[:, -shifts[1]:]
    return a_
        
def embedMatrix(block, wall, position, mode='center'):
    """ Embeds a small matrix into a bigger one. If a length-2 tuple is given instead of a big matrix, a zero matrix of that size is used. """
    if type(wall) == tuple:
        wall = np.zeros(wall, dtype=block.dtype)
    else:
        wall = wall.copy()
    try: 
        if mode == 'corner':
            wall[position[0] : position[0] + block.shape[0], position[1] : position[1] + block.shape[1]] = block
        if mode == 'center':
            wall[position[0]-block.shape[0]/2 : position[0]-block.shape[0]/2 + block.shape[0], position[1]-block.shape[1]/2 : position[1]-block.shape[1]/2 + block.shape[1]] = block
    except ValueError:
        raise ValueError('Trying to put embedded matrix outside the boundaries of the embedding matrix.')
    return wall
    
def shiftAndMultiply(block, wall, position, mode='center'):
    """ Does the same as embedMatrix() but returns the product of the two, with dimensions of the small matrix. """
    try: 
        if mode == 'corner':
            return block * wall[position[0] : position[0] + block.shape[0], position[1] : position[1] + block.shape[1]]
        if mode == 'center':
            return block * wall[position[0]-block.shape[0]/2 : position[0]-block.shape[0]/2 + block.shape[0], position[1]-block.shape[1]/2 : position[1]-block.shape[1]/2 + block.shape[1]]
    except ValueError:
        print block.shape, wall.shape, position
        raise ValueError('Shifting out of bounds.')

def rotate_coords(x, y, z, theta, axis=0):
    """ 
    Rotates x y z coordinates (of any shape) around the specified axis.
    Follows the right hand convention at least when 
    x, y, z = np.indices(shape).

    Arguments:
    x, y, z     Coordinates
    theta       angle in degrees

    Keyword arguments:
    axis        The axis around which to rotate. Defaults to 0.

    Returns:
    X, Y, Z     The rotated coordinates.
    """

    theta = -theta / 180. * np.pi

    assert axis in (0, 1, 2)

    if axis == 0:
        A = np.array(
            [[1, 0,              0],
             [0, np.cos(theta), -np.sin(theta)],
             [0, np.sin(theta),  np.cos(theta)]])
    elif axis == 1:
        A = np.array(
            [[np.cos(theta), 0, np.sin(theta)],
             [0, 1, 0],
             [-np.sin(theta), 0, np.cos(theta)]])
    elif axis == 2:
        A = np.array(
            [[np.cos(theta), -np.sin(theta), 0],
             [np.sin(theta), np.cos(theta), 0],
             [0, 0, 1]])
    x_ = A[0,0] * x + A[0,1] * y + A[0,2] * z
    y_ = A[1,0] * x + A[1,1] * y + A[1,2] * z
    z_ = A[2,0] * x + A[2,1] * y + A[2,2] * z
    return x_, y_, z_

def rotate_3d_array(A, angles=[0, 0, 0], center=None, **kwargs):
    """ 
    Rotates the data content of a 3D array around its middle or
    specified center by interpolation. Rotations are done sequentially
    around the first, second and third axes.

    Arguments:
    A           Input 3D array

    Keyword arguments:
    angles      Three angles, one for each rotation axis. Defaults to
                [0., 0., 0.]
    center      The array index around which to rotate. Defaults to the
                center of the array.
    **kwargs    Forwarded to scipy.ndimage.map_coordinates

    Returns:
    B           Array of rotated data
    """

    if not center:
        center = np.array(A.shape) / 2

    # start with a a full set of 3d indices
    i, j, k = np.indices(A.shape)

    # rotate around the center
    i -= center[0]
    j -= center[1]
    k -= center[2]
    for ii in (0, 1, 2):
        i, j, k = rotate_coords(i, j, k, angles[ii], axis=ii)
    i += center[0]
    j += center[1]
    k += center[2]

    # evaluate the array on this grid
    rotated = map_coordinates(A, [i, j, k], **kwargs)

    return rotated
