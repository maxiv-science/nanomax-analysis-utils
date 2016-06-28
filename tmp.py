# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import helpers

import scipy.misc
a = scipy.misc.face()
print a.shape
b = helpers.binPixels(a, n=2)
print b.shape

import matplotlib.pyplot as plt
plt.imshow(b, interpolation='none')