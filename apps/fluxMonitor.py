import time
import matplotlib.pyplot as plt
plt.ion()
from PyTango import DeviceProxy, DevFailed
from nmutils.utils.ion_chamber import Ionchamber

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-t', '--tight',
                  action='store_true', dest = 'tight', default=False,
                  help='Keep tight limits for y axis.')
(options, args) = parser.parse_args()

NMAX = 50

mono = DeviceProxy('pseudomotor/nanomaxenergy_ctrl/1')
em = DeviceProxy('test/alebjo/alba2')
ic = Ionchamber(length=1.5, gas='air')

def on_close(evt):
    print('Window closed!')
    exit(0)

fig = plt.figure()
fig.canvas.mpl_connect('close_event', on_close)
ax = plt.gca()
lines = []
last = None

n = 0
while True:
    try:
        current = em.instant_current_1
        energy = mono.position
    except DevFailed:
        continue
    flux = ic.flux(current, energy)
    if last is None:
        last = flux
        continue
    n += 1
    lines.append(plt.plot((n-1, n), (last, flux), 'r'))
    if len(lines) > NMAX:
        l = lines.pop(0)[0].remove()
    ax.set_xlim(max(0, n-NMAX), max(NMAX, n))
    #ax.set_ylim(bottom=0) # ruins autoscaling
    if options.tight:
        Y = [lines[0][0].get_ydata()[0]] +\
            [line[    0].get_ydata()[1] for line in lines]
        Ye = (max(Y)-min(Y)) * .1
        ax.set_ylim(min(Y)-Ye,max(Y)+Ye)
    last = flux
    fig.suptitle('Flux: %.2e photons/s' % flux, fontsize=24)
    fig.canvas.start_event_loop(.001)
    time.sleep(.2)
