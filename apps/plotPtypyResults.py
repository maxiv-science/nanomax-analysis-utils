import numpy as np
import matplotlib.pyplot as plt
import nmutils
import h5py
import matplotlib.gridspec as gridspec
import argparse
from mpl_toolkits.axes_grid1 import make_axes_locatable

"""
This script visualizes the output of a ptypy run, by loading a ptyr file.
"""

### Parse input
parser = argparse.ArgumentParser(
    description='This script visualizes the output of a ptypy run, by loading a ptyr file.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('ptyr_file', type=str,
                    help='a ptypy reconstruction file')
parser.add_argument('--no-window',
                    action='store_const', const=True,
                    dest='not_interactive',
                    help='switches on or off live plotting')
parser.add_argument('--title', type=str, dest='title',
                    help='the plot title')
parser.add_argument('--output', type=str, dest='output',
                    help='image file name for saving')
parser.add_argument('--backward', type=float, dest='bw',
                    default=1000.0,
                    help='backward propagation in microns, defaults to ')
parser.add_argument('--forward', type=float, dest='fw',
                    default=1000.0,
                    help='forward propagation in microns')
parser.add_argument('--positions', type=int, dest='steps',
                    default=200,
                    help='number of planes along the optical axis')
parser.add_argument('--flipx',
                    action='store_const', const=True,
                    dest='flipx',
                    help='flips the x axis about the origin')
parser.add_argument('--flipy',
                    action='store_const', const=True,
                    dest='flipy',
                    help='flips the y axis about the origin')
args = parser.parse_args()

if args.title is None:
    args.title = args.ptyr_file if '/' not in args.ptyr_file else args.ptyr_file.split('/')[-1]

backProp, forwProp = -args.bw, args.fw
outputFile = args.output
inputFile = args.ptyr_file
title = args.title
interactive = not args.not_interactive
steps = args.steps
flipx = args.flipx
flipy = args.flipy

if outputFile is not None:
    outputPrefix = outputFile.split('.')[0]
    try:
        outputSuffix = outputFile.split('.')[1]
    except IndexError:
        outputSuffix = 'png'

### load reconstruction data
with h5py.File(inputFile, 'r') as hf:
    scanid = str(hf['content/probe'].keys()[0])
    print 'loading entry %s' % scanid
    probe = np.array(hf.get('content/probe/%s/data' % scanid))
    obj = np.array(hf.get('content/obj/%s/data' % scanid))
    psize = np.array(hf.get('content/probe/%s/_psize' % scanid))
    energy = np.array(hf.get('content/probe/%s/_energy' % scanid))
    origin = np.array(hf.get('content/probe/%s/_origin' % scanid))

try:
    probe = probe[0]
    obj = obj[0]
    psize = psize[0]
except IndexError:
    raise IOError('That doesn''t look like a valid reconstruction file!')
print "Loaded probe %d x %d and object %d x %d, pixel size %.1f nm, energy %.2f keV"%(probe.shape + obj.shape + (psize*1e9, energy))

### define distances and propagate
dist = np.linspace(backProp, forwProp, steps) * 1e-6
dx = dist[1] - dist[0]
print "propagating to %d positions separated by %.1f um..."\
    % (len(dist), dx*1e6)
### not sure why, but the propagation goes in the other direction here!
### it could be a misunderstanding about motors at nanomax...
field3d = nmutils.utils.propagateNearfield(probe, psize, -dist, energy)

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
ax_vertical.imshow(power_vertical, cmap='gray', extent=[1e6*dist[0], 1e6*dist[-1], -1e6*psize*probe.shape[0]/2, 1e6*psize*probe.shape[1]/2], interpolation='none')
ax_vertical.axvline(x=focus_vertical_x*1e6, lw=1, ls='--', color='r')
ax_vertical.text(1e6*focus_vertical_x, ax_vertical.get_ylim()[0] + .2*np.diff(ax_vertical.get_ylim())[0], 
    ' %.0f um '%(1e6*focus_vertical_x), color='red', 
    ha=('right' if focus_vertical_x<focus_x else 'left'))
ax_vertical.axvline(x=focus_x*1e6, lw=2, ls='-', color='r')
ax_vertical.text(1e6*focus_x, ax_vertical.get_ylim()[0] + .8*np.diff(ax_vertical.get_ylim())[0],
    ' %.0f um '%(1e6*focus_x), color='red', va='top',
    ha=('right' if focus_vertical_x>focus_x else 'left'))
ax_vertical.set_aspect('auto')
ax_horizontal.imshow(power_horizontal, cmap='gray', extent=[1e6*dist[0], 1e6*dist[-1], -1e6*psize*probe.shape[0]/2, 1e6*psize*probe.shape[1]/2], interpolation='none')
ax_horizontal.axvline(x=focus_horizontal_x*1e6, lw=1, ls='--', color='r')
ax_horizontal.text(1e6*focus_horizontal_x, ax_horizontal.get_ylim()[0] + .2*np.diff(ax_horizontal.get_ylim())[0],
    ' %.0f um '%(1e6*focus_horizontal_x), color='red',
    ha=('right' if focus_horizontal_x<focus_x else 'left'))
ax_horizontal.axvline(x=focus_x*1e6, lw=2, ls='-', color='r')
ax_horizontal.set_aspect('auto')
ax_horizontal.set_ylabel('$\mu$m', y=1.05)
for tk in ax_vertical.get_xticklabels(): tk.set_visible(False)
ax_horizontal.set_xlabel('beamline z axis ($\mu$m)', fontsize=16)

lblue = (.3,.3,1.0)
ax_vertical.axvline(x=0, lw=1, ls='--', color=lblue)
ax_horizontal.axvline(x=0, lw=1, ls='--', color=lblue)
ax_horizontal.text(0, ax_horizontal.get_ylim()[0] + .01*np.diff(ax_horizontal.get_ylim())[0], 
    ' sample ', color=lblue, va='bottom',
    ha=('left' if focus_x < 0 else 'right'))

ax_horizontal.text(1.05, 0.5, 'horizontal focus (M2)',
     horizontalalignment='center',
     verticalalignment='center',
     rotation=90,
     transform = ax_horizontal.transAxes)
ax_vertical.text(1.05, 0.5, 'vertical focus (M1)',
     horizontalalignment='center',
     verticalalignment='center',
     rotation=90,
     transform = ax_vertical.transAxes)

plt.suptitle(title, fontsize=20)
if outputFile is not None:
    fn = outputPrefix + '_probe.' + outputSuffix
    plt.savefig(fn)
    print 'Saved to %s'%fn

### Object
fig, ax = plt.subplots(ncols=2, figsize=(10,6), sharex=True, sharey=True)
plt.subplots_adjust(wspace=.3)
fig.suptitle(title, fontsize=20)

if flipx:
    obj = np.fliplr(obj)
if flipy:
    obj = np.flipud(obj)
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
#img = ax[1].imshow(np.angle(obj), vmin=-.1, vmax=.2, cmap='hsv', extent=extent, interpolation='none')
plt.setp(ax[1].xaxis.get_majorticklabels(), rotation=70 )
ax[1].set_xlabel('$\mu$m')
divider = make_axes_locatable(ax[1])
cax = divider.append_axes("right", size="5%", pad=0.05)
cb = plt.colorbar(img, cax=cax, ticks=(-np.pi, -np.pi/2, 0, np.pi/2, np.pi))
cb.ax.set_yticklabels(['-$\pi$', '-$\pi/2$', '0', '$\pi/2$', '$\pi$'])
ax[1].set_title('Phase')

if outputFile is not None:
    fn = outputPrefix + '_object.' + outputSuffix
    plt.savefig(fn)
    print "Saved to %s"%fn

if interactive:
    plt.show()
