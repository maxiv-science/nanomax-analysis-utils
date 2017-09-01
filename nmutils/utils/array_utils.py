""" Isolated helper functions for array operations. """

import numpy as np

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
