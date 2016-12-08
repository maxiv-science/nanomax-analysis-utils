import numpy as np
import matplotlib.pyplot as plt
import h5py
import ptypy
import nmutils
import matplotlib.gridspec as gridspec
import sys
from mpl_toolkits.axes_grid1 import make_axes_locatable

"""
This script visualizes the output of a ptypy run, by loading a ptyr or ptyd file.
"""

### Parse input
if len(sys.argv) < 2 or len(sys.argv) > 6:
    print "\nUsage: reconstructionAnalysis.py <ptyd file> [<title> <output file>"
    print   "                                 <back propagation um> <forward propagation um>] \n"
    print "If an output file isn't specified or is 'None', the plot will be interactive.\n"
    exit()
inputFile = sys.argv[1]
title = ''
outputFile = None
backProp = -1000
forwProp = 1000
if len(sys.argv) >= 3:
    title = sys.argv[2]
if len(sys.argv) >= 4:
    outputFile = sys.argv[3]
    outputPrefix = outputFile.split('.')[0]
    try:
        outputSuffix = outputFile.split('.')[1]
    except IndexError:
        outputSuffix = 'png'
if len(sys.argv) >= 5:
    backProp = float(sys.argv[4])
if len(sys.argv) >= 6:
    forwProp = float(sys.argv[5])

### load reconstruction data
with h5py.File(inputFile, 'r') as hf:
    probe = np.array(hf.get('content/probe/S00G00/data'))[0]
    obj = np.array(hf.get('content/obj/S00G00/data'))[0]
    psize = np.array(hf.get('content/probe/S00G00/_psize'))[0]
    energy = np.array(hf.get('content/probe/S00G00/_energy'))
    origin = np.array(hf.get('content/probe/S00G00/_origin'))
print "Loaded probe %d x %d and object %d x %d, pixel size %.1f nm, energy %.2f keV"%(probe.shape + obj.shape + (psize*1e9, energy))

### define distances and propagate
dist = np.linspace(backProp, forwProp, 200) * 1e-6
dx = dist[1] - dist[0]
print "propagating to %d positions..."%len(dist)
field3d = nmutils.utils.propagateNearfield(probe, psize, dist, energy)

### get intensities and focii
power3d = np.abs(field3d)**2
power_vertical = np.sum(power3d, axis=2).T
power_horizontal = np.sum(power3d, axis=1).T
focus_vertical_ind = np.argmax(np.sum(power_vertical**2, axis=0))
focus_vertical_x = dist[focus_vertical_ind]
focus_horizontal_ind = np.argmax(np.sum(power_horizontal**2, axis=0))
focus_horizontal_x = dist[focus_horizontal_ind]
focus_ind = np.argmax(np.sum(power3d**2, axis=(1,2)))
focus_x = dist[focus_ind]
focus = field3d[focus_ind]

### plot
fig = plt.figure(figsize=(8, 10))
outer_grid = gridspec.GridSpec(2, 2, wspace=.2, hspace=.2, height_ratios=[2,3])

# probe and focus spots
def spot_subplot(gridcell, data, shareax=None, title=''):
    subgrid = gridspec.GridSpecFromSubplotSpec(2, 2, subplot_spec=gridcell, width_ratios=[3,1], height_ratios=[1,3], hspace=.05, wspace=.05)
    lims = [-1e6*data.shape[0] * psize / 2, 1e6*data.shape[0] * psize / 2] # um
    posrange = np.linspace(lims[0], lims[1], data.shape[0])
    ax = plt.subplot(subgrid[1,0], sharex=shareax, sharey=shareax)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=70 )
    ax.imshow(nmutils.utils.complex2image(data), extent=lims+[lims[1], lims[0]], interpolation='none')
    ax_histh = plt.subplot(subgrid[0,0], sharex=ax, yticklabels=[], ylabel='Int.')
    ax_histv = plt.subplot(subgrid[1,1], sharey=ax, xticklabels=[], xlabel='Int.')
    ax_histv.plot(np.sum(np.abs(data)**2, axis=1), posrange)
    ax_histh.plot(posrange, np.sum(np.abs(data)**2, axis=0))
    ax_histh.set_title(title, x=.67)
    for tk in ax_histh.get_xticklabels(): tk.set_visible(False)
    for tk in ax_histv.get_yticklabels(): tk.set_visible(False)

    # FWHM:
    import scipy.interpolate
    for i in (0,1):
        y = np.sum(np.abs(data)**2, axis=i)
        edges = scipy.interpolate.UnivariateSpline(posrange, y-y.max()/2).roots()
        r1, r2 = edges[0], edges[-1]
        if i == 0:
            ax_histh.axvspan(r1, r2, fc='r', alpha=.3)
            ax_histh.text(r2, np.mean(ax_histh.get_ylim()), ' %.0f nm'%((r2-r1)*1e3), fontsize=10, rotation=-90*i)
            ax.set_xlim(np.mean([r1,r2]) + np.array([-1,1]))
        elif i == 1:
            ax_histv.axhspan(r1, r2, fc='r', alpha=.3)
            ax_histv.text(np.mean(ax_histv.get_xlim()), r1, ' %.0f nm'%((r2-r1)*1e3), fontsize=10, va='top', ha='center', rotation=-90)
            ax.set_ylim(np.mean([r1,r2]) + np.array([-1,1]))
    return ax
a = spot_subplot(outer_grid[0,0], probe, title='Sample plane')
a.set_ylabel('$\mu$m')
b = spot_subplot(outer_grid[0,1], focus, shareax=a, title='Focal plane')

# beam profiles
subgrid = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=outer_grid[1,:], hspace=.05)
ax_vertical = plt.subplot(subgrid[0])
ax_horizontal = plt.subplot(subgrid[1], sharex=ax_vertical, sharey=ax_vertical)
ax_vertical.imshow(power_vertical, cmap='gray', extent=[1e6*dist[0], 1e6*dist[-1], -1e6*psize*probe.shape[0]/2, 1e6*psize*probe.shape[1]/2])
ax_vertical.axvline(x=focus_vertical_x*1e6, lw=1, ls='--', color='r')
ax_vertical.text(1e6*focus_vertical_x, ax_vertical.get_ylim()[0] + .2*np.diff(ax_vertical.get_ylim())[0], '%.0f um '%(1e6*focus_vertical_x), color='red', ha='right')
ax_vertical.axvline(x=focus_x*1e6, lw=2, ls='-', color='r')
ax_vertical.text(1e6*focus_x, ax_vertical.get_ylim()[0] + .2*np.diff(ax_vertical.get_ylim())[0], ' %.0f um'%(1e6*focus_x), color='red', ha='left')
ax_vertical.set_aspect('auto')
ax_horizontal.imshow(power_horizontal, cmap='gray', extent=[1e6*dist[0], 1e6*dist[-1], -1e6*psize*probe.shape[0]/2, 1e6*psize*probe.shape[1]/2])
ax_horizontal.axvline(x=focus_horizontal_x*1e6, lw=1, ls='--', color='r')
ax_horizontal.text(1e6*focus_horizontal_x, ax_horizontal.get_ylim()[0] + .2*np.diff(ax_horizontal.get_ylim())[0], ' %.0f um'%(1e6*focus_horizontal_x), color='red')
ax_horizontal.axvline(x=focus_x*1e6, lw=2, ls='-', color='r')
ax_horizontal.set_aspect('auto')
ax_horizontal.set_ylabel('$\mu$m', y=1.05)
for tk in ax_vertical.get_xticklabels(): tk.set_visible(False)

plt.suptitle(title, fontsize=20)
if outputFile and (not outputFile.lower() == 'none'):
    fn = outputPrefix + '_probe.' + outputSuffix
    plt.savefig(fn)
    print 'Saved to %s'%fn

### Object
fig, ax = plt.subplots(ncols=2, figsize=(10,6), sharex=True, sharey=True)
plt.subplots_adjust(wspace=.3)
fig.suptitle(title, fontsize=20)
extent = 1e6 * np.array([origin[0], origin[0]+(obj.shape[1]-1)*psize, origin[1], origin[1]+(obj.shape[0]-1)*psize])

# amplitude
mag = np.abs(obj)
mag_cut = mag[mag.shape[0]/3:2*mag.shape[0]/3, mag.shape[1]/3:2*mag.shape[1]/3] # to find relevant dynamic range
vmin = mag_cut.min()
vmax = mag_cut.max()
img = ax[0].imshow(mag, cmap='gray', extent=extent, vmin=vmin, vmax=vmax, interpolation='none')
plt.setp(ax[0].xaxis.get_majorticklabels(), rotation=70)
ax[0].set_ylabel('$\mu$m')
ax[0].set_xlabel('$\mu$m')
divider = make_axes_locatable(ax[0])
cax = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(img, cax=cax)
ax[0].set_title('Amplitude')

# phase
img = ax[1].imshow(np.angle(obj), vmin=-np.pi, vmax=np.pi, cmap='hsv', extent=extent, interpolation='none')
plt.setp(ax[1].xaxis.get_majorticklabels(), rotation=70 )
ax[1].set_xlabel('$\mu$m')
divider = make_axes_locatable(ax[1])
cax = divider.append_axes("right", size="5%", pad=0.05)
cb = plt.colorbar(img, cax=cax, ticks=(-np.pi, -np.pi/2, 0, np.pi/2, np.pi))
cb.ax.set_yticklabels(['-$\pi$', '-$\pi/2$', '0', '$\pi/2$', '$\pi$'])
ax[1].set_title('Phase')

if outputFile and (not outputFile.lower() == 'none'):
    fn = outputPrefix + '_object.' + outputSuffix
    plt.savefig(fn)
    print "Saved to %s"%fn

if (not outputFile) or (outputFile.lower() == 'none'):
    plt.show()
