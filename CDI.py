#!/usr/bin/python
# -*- coding: utf-8 -*-

# This implements the input/output algorithm described in Fienup1978

import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np
import time
import statprof
import helpers
statprof.start()
plt.ion()

PLOT = True
N = 1000000
beamStopSize = 4#4
shrinkWrapN = 100
shrinkWrapSigmaTight = 20
shrinkWrapSigmaLoose = 5#7
shrinkWrapThreshold = .2#2#.15
startHIO = 0
keepSupportTogether = True
allowSupportHoles = False # not implemented
enforceRealness = False # this messes up shrink wrap. suspicious. is there something fishy with shrink wrap?
beta = 0.5
photons = 0 #0 means don't apply noise
outputN = 10

#%%% Define the sample

sample = plt.imread('canoe_SEM_ed.png');
sample = sample / sample.max()

# pad the image to make a square matrix
#sample = np.pad(sample, ((0,0), (1,0)), mode='constant'); print "ad hoc padding"
minPad = 100 # add these many zeros to the image's largest dimension on each side
maxAx = np.where(sample.shape == np.max(sample.shape))[0][0]
minAx = int(not maxAx)
pads = [(0,0), (0,0)]
pads[maxAx] = (minPad,) * 2
pads[minAx] = (minPad + (sample.shape[maxAx] - sample.shape[minAx]) / 2,) * 2
sample = np.pad(sample, pads, mode='constant')

#%%% Define the support
linRatios = (.45, .45)
midPoint = tuple(np.array(sample.shape) / 2)
supportBox = ((midPoint[0] - sample.shape[0] * linRatios[0] / 2, midPoint[0] + sample.shape[0] * linRatios[0] / 2),
              (midPoint[1] - sample.shape[1] * linRatios[1] / 2, midPoint[1] + sample.shape[1] * linRatios[1] / 2) )
support = np.zeros(sample.shape, dtype=int)
support[supportBox[0][0]:supportBox[0][1], supportBox[1][0]:supportBox[1][1]] = 1

#%%% Transform the sample to get the image

image = helpers.fft(sample)

# fake a beamstop
a, b = image.shape
invBeamStop = np.ones(image.shape)
if beamStopSize:
    invBeamStop[a/2-beamStopSize:a/2+beamStopSize, b/2-beamStopSize:b/2+beamStopSize] = 0
    invBeamStop[a/2-1:a/2+1, :b/2] = 0
beamStop = 1 - invBeamStop
beamStopMask = np.where(beamStop)
image *= invBeamStop

imageIntensity = np.abs(image)**2
if photons:
    imageIntensity = helpers.noisyImage(imageIntensity, photons)
imageAmplitude = np.sqrt(imageIntensity)
print imageIntensity.min(), imageIntensity.max()

if PLOT:
    fig = plt.figure(figsize=(14,10))
    gs = gridspec.GridSpec(2, 3)
    ax = []
    ax += [fig.add_subplot(gs[0, 0], title='original image')]
    ax += [fig.add_subplot(gs[0, 1])]
    ax += [fig.add_subplot(gs[0, 2], title='ill-defined errors')]
    ax += [fig.add_subplot(gs[1, 0], sharex=ax[0], sharey=ax[0])]
    ax += [fig.add_subplot(gs[1, 1])]
    ax += [fig.add_subplot(gs[1, 2])]
    a2 = ax[2].twinx()
    opts = {'cmap':'gray', 'interpolation':'none'}
    ax[0].imshow(np.abs(sample), **opts);
    ax[0].set_title('original image')

#%%% Iteratively retrieve the phases

phases = np.random.rand(*image.shape) * 2 * np.pi
image = imageAmplitude * np.exp(1j * phases)
imageErrors, sampleErrors = [], []
tmp = []
norm = np.sum(imageAmplitude**2)
oldSample = support
for i in range(N):
    t0 = time.time()
    # transform to real space
    t0 = time.time() * 1000
    sample = helpers.ifft(image)
    tmp.append(time.time()*1000 - t0)
        
    # enforce real space constraints
    if i > startHIO:
        # HIO
        sample = support * sample + (1 - support) * (oldSample - sample * beta) # this is faster than using np.where(1-support), even if the indices are saved before
    else:
        # Error reduction
        sample = support * sample
        #sample = np.abs(sample)
    
    # This is a reasonable constraint but for some reason messes up the shrink wrapping
    if enforceRealness:
        sample = np.abs(sample)

    # shrink wrap the support    
    if (i % shrinkWrapN == 0) and (i > 0):
        #sigma = {False: shrinkWrapSigmaLoose, True: shrinkWrapSigmaTight}[i > 300]
        sigma = max(shrinkWrapSigmaTight, int(round(shrinkWrapSigmaLoose - (shrinkWrapSigmaLoose - shrinkWrapSigmaTight) * i / 3000.0)))
        blurredSample = helpers.smoothImage(sample, sigma)
        # working with amplitudes here, numpy.ndarray.max() only looks at real part.
        support = ( np.abs(blurredSample) >= shrinkWrapThreshold * np.max(np.abs(blurredSample)) )
        medians = [np.median(np.where(support)[0]), np.median(np.where(support)[1])]
        centers = np.array(support.shape) / 2
        shifts = centers - medians
        support = helpers.shift(support, shifts)
        if keepSupportTogether:
            support = helpers.biggestBlob(support)
        sample = helpers.shift(sample, shifts)

    oldSample = sample #

    # show the current state
    if (i % outputN == 0) and PLOT:
        try: 
            ax[2].plot([i-outputN, i], sampleErrors[-2:], 'k-')
            a2.plot([i-outputN, i], imageErrors[-2:], 'r-')
        except: pass
        ax[1].clear()
        ax[1].imshow(support, **opts)
        ax[1].set_title('refined support')
        ax[3].clear()
        ax[3].imshow(np.abs(sample), **opts)
        ax[3].set_title('reconstructed amplitude')
        ax[4].clear()
        ax[4].imshow(np.log10(imageIntensity), **opts)
        ax[4].hold(True)
        ax[4].imshow(beamStop, cmap=helpers.alpha2red, interpolation='none')
        #ax[4].imshow(np.angle(sample)+np.pi)
        #ax[4].set_title('reconstructed phase')
        plt.draw()
        plt.pause(.001)
        
    # transform to q space
    image = helpers.fft(sample)
    
    if (i % outputN == 0) and PLOT:
        ax[5].clear()
        ax[5].imshow(np.log10(np.abs(image)**2), **opts);
        ax[5].set_title('model diffraction')
        imageErrors.append(np.sum( (np.abs(image) * invBeamStop - imageAmplitude * invBeamStop)**2 )) # Fourier space errors according to Fienup1978
        sampleErrors.append(np.sum((1-support) * np.abs(sample)**2) / np.sum(np.abs(sample)**2))

    # combine experimental amplitudes with iterative phases (Fourier space constraints)
    # the second term uses the transform of the trial object to replace pixels lost behind the beamstop
    image = invBeamStop * imageAmplitude * np.exp(1j * np.angle(image)) + beamStop * image

    if (i % outputN == 0):
        print 'Iteration: %04d, Sample error: %.4f, Intensity error: %.0f'%(i, sampleErrors[-1], imageErrors[-1]) # 60 us

print np.mean(tmp)
plt.savefig('fig.png')

statprof.stop()
#statprof.display()
