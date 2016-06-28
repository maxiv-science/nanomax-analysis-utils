import matplotlib.pyplot as plt
from matplotlib import gridspec
import numpy as np
import statprof
import helpers
import random
import scipy.misc
statprof.start()
plt.ion()

#wieno7Shoop7

PLOT = True
N = 10000
beamStopSize = 0
retrieveProbeAfter = 0
alpha = 1.
beta = 0.
photons = 0 #0 means don't apply noise
outputN = 10
maxProbeSize = 100
linearOverlap = 2.5
randomOrder = False
randomDisplacement = 0

#%%% Define the true sample and probe

sample = np.mean(scipy.misc.face(), axis=2)
sample = helpers.binPixels(sample, 3)
#sample = plt.imread('Photon-noise.jpg')
#sample = plt.imread('canoe_SEM_ed.png')
#sample = plt.imread('NanoMax_Text_width_1um_ed.png')
#sample = np.pad(sample, maxProbeSize/2, mode='constant')
probe = helpers.circle(maxProbeSize, dtype='complex128')
#probe = np.ones((maxProbeSize, maxProbeSize))

#%%% Define the scanning positions
nPositions = [int(round(sample.shape[0] / maxProbeSize * linearOverlap)), int(round(sample.shape[1] / maxProbeSize * linearOverlap))]
positions = []
vGrid = np.arange(maxProbeSize/2 + randomDisplacement, sample.shape[0], (sample.shape[0]-maxProbeSize)/(nPositions[0]-1))
hGrid = np.arange(maxProbeSize/2 + randomDisplacement, sample.shape[1], (sample.shape[1]-maxProbeSize)/(nPositions[1]-1))
for i in range(nPositions[0]):
    for j in range(nPositions[1]):
        positions.append(np.array([vGrid[i] + random.randint(-randomDisplacement, randomDisplacement), hGrid[j] + random.randint(-randomDisplacement, randomDisplacement) ]))
    
#%%% Generate the mock data
imageAmplitudes = []
for i in range(len(positions)):
    exitWave = helpers.shiftAndMultiply(probe, sample, positions[i], mode='center')
    image = helpers.fft(exitWave)
    
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
    imageAmplitudes.append(np.sqrt(imageIntensity))
    
if PLOT:
    fig = plt.figure(figsize=(14,10))
    gs = gridspec.GridSpec(2, 3)
    ax = []
    ax += [fig.add_subplot(gs[0, 0], title='original image')]
    ax += [fig.add_subplot(gs[0, 1], sharex=ax[0], sharey=ax[0])]
    ax += [fig.add_subplot(gs[0, 2], title='ill-defined errors')]
    ax += [fig.add_subplot(gs[1, 0])]
    ax += [fig.add_subplot(gs[1, 1])]
    ax += [fig.add_subplot(gs[1, 2])]
    a2 = ax[2].twinx()
    opts = {'cmap':'gray', 'interpolation':'none'}
    ax[0].imshow(np.abs(sample), **opts);
    ax[0].set_title('original image')
    for i in range(len(positions)):
        ax[0].plot(positions[i][1], positions[i][0], '.r')
    plt.pause(.01)

#for i in range(len(positions)):
#    ax[1].imshow(np.log10(imageAmplitudes[i]**2), cmap='gray')
#    plt.draw()
#    time.sleep(.3)

#%%% Iteratively retrieve the phases

# starting guesses
sample = np.zeros(sample.shape, dtype='complex128')
#probe = np.ones((maxProbeSize,maxProbeSize), dtype='complex128')
#probe = helpers.pseudoCircle(maxProbeSize, radius=None, exponent=2.5, dtype='complex128')

order = range(len(positions))
for i in range(N):
    print i
    if randomOrder:
        random.shuffle(order)
    for j in range(len(positions)):
        position_ = positions[order[j]]
        exitWave = helpers.shiftAndMultiply(probe, sample, position_, mode='center')
        image = helpers.fft(exitWave)
        image = invBeamStop * imageAmplitudes[order[j]] * np.exp(1j * np.angle(image)) + beamStop * image
        exitWave_ = helpers.ifft(image)
        shiftedProbe = helpers.embedMatrix(probe, sample.shape, position_, mode='center')
        sample += alpha * np.conj(shiftedProbe) / np.max(np.abs(shiftedProbe))**2 * helpers.embedMatrix((exitWave_ - exitWave), sample.shape, position_, mode='center')
        if i > retrieveProbeAfter:
            cutSample = sample[position_[0] - maxProbeSize/2 : position_[0] + maxProbeSize/2, position_[1] - maxProbeSize/2 : position_[1] + maxProbeSize/2]
            probe  +=  beta * np.conj(cutSample) / np.max(np.abs(cutSample))**2 * (exitWave_ - exitWave)
        if PLOT:
            ax[1].clear()
            ax[1].imshow(np.abs(sample), cmap='gray') 
            ax[1].imshow(np.abs(shiftedProbe), cmap=helpers.alpha2redTransparent)
            ax[2].clear()
            ax[2].imshow(np.abs(probe), cmap='gray', vmin=0, vmax=1.5)
            ax[3].clear()
            ax[3].imshow(np.log10(imageAmplitudes[order[j]]**2), interpolation='none')
            ax[4].clear()
            #ax[4].imshow(np.abs(helpers.embedMatrix((exitWave-exitWave_), sample.shape, position_, mode='center')), cmap='gray')
            ax[4].imshow(np.log10(np.abs(image)**2), interpolation='none')
            #ax[5].clear()
            ax[5].plot(j + len(positions) * i, np.log10(np.sum(np.abs(probe))), '.k')
            ax[5].plot(j + len(positions) * i, np.log10(np.sum(np.abs(sample))), '.r')
            #ax[5].imshow(np.abs(cutSample), cmap='gray')
            plt.draw()
            plt.pause(.01)
