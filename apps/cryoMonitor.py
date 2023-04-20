import time
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
plt.ion()
from PyTango import DeviceProxy, DevFailed



from optparse import OptionParser
parser = OptionParser()
parser.add_option('-t', '--tight',
                  action='store_true', dest = 'tight', default=False,
                  help='Keep tight limits for y axis.')
(options, args) = parser.parse_args()

NMAX = 1000
buffer_level = DeviceProxy('B303A-A100330/CRY/CCLR-01')


def on_close(evt):
    print('Window closed!')
    exit(0)

fig = plt.figure()
fig.canvas.manager.set_window_title('cryoMonitor')
fig.canvas.mpl_connect('close_event', on_close)
ax = plt.gca()
ax.set_ylim(0,100)
plt.grid()
plt.axhline(y=25, c='k', ls='--', alpha=0.5)
plt.subplots_adjust(top=0.85)

values = []
times = []
plot_data = None
str_refill = '-:-:-'


n = 0
while True:

    # grab a new data point
    try:
        new_value = buffer_level.L2Level_MON
        new_time = datetime.now()
    except DevFailed:
        continue
    values.append(new_value)
    times.append(new_time)

    # if data buffer gets too long, delete every 2nd element
    if len(values)>=NMAX:
        del values[::2]
        del times[::2]

    # if enough data, extrapolate to when automatic refill happens
    if len(values)>=200:
        y = mdates.date2num(times[:-100])
        x = values[:-100]
        params = np.polyfit(x, y, 1)
        f_lin = np.poly1d(params)
        t_refill = mdates.num2date(f_lin(25))
        str_refill = t_refill.strftime("%H:%M:%S")


    # update the plot
    if plot_data == None:
        plot_data, = plt.plot([new_time, datetime.now()], [new_value, new_value], c='r')
    else:
        plot_data.set_xdata(times)
        plot_data.set_ydata(values)
        fig.canvas.draw()
        fig.canvas.flush_events()
        ax.set_xlim(times[0],times[-1])

    # update the figure
    fig.suptitle(f'current mono L2 level: {new_value:.1f}%\nestimated refill time: {str_refill}', fontsize=18)
    fig.canvas.start_event_loop(.01)

    # wait a bit before asking for the next data point
    # waiting time depends on the number of data points in the buffer
    if len(values)<=1: 
        time.sleep(0.1)
    elif len(values)<=100: 
        time.sleep(0.3)
    else: 
        time.sleep(1.0)