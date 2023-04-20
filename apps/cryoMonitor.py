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

NMAX = 2000
cryocooler = DeviceProxy('B303A-A100330/CRY/CCLR-01')


def on_close(evt):
    print('Window closed!')
    exit(0)

fig = plt.figure()
fig.canvas.manager.set_window_title('cryoMonitor')
fig.canvas.mpl_connect('close_event', on_close)
ax = plt.gca()
ax.set_ylim(0,100)
plt.grid()
plt.axhline(y=25, c='r', ls='--', alpha=0.8)
plt.subplots_adjust(top=0.85)

values_L1 = []
values_L2 = []
times = []
plot_data_L1 = None
plot_data_L2 = None
str_refill = '-:-:-'


n = 0
while True:

    # grab a new data point
    try:
        new_value_L1 = cryocooler.L1Level_MON
        new_value_L2 = cryocooler.L2Level_MON
        new_time = mdates.date2num(datetime.now())
    except DevFailed:
        continue
    values_L1.append(new_value_L1)
    values_L2.append(new_value_L2)
    times.append(new_time)

    # if data buffer gets too long, delete every 2nd element
    if len(times)>=NMAX:
        values_L1 = [0.5*(values_L1[i-1]+values_L1[i]) for i, v in enumerate(values_L1) if i%2==1]
        values_L2 = [0.5*(values_L2[i-1]+values_L2[i]) for i, v in enumerate(values_L2) if i%2==1]
        times = [0.5*(times[i-1]+times[i]) for i, v in enumerate(times) if i%2==1 ]

    # if enough data, extrapolate to when automatic refill happens
    if len(values_L2)>=1500:
        y = times[:-1500] #mdates.date2num(times[:-100])
        x = values_L2[:-1500]
        params = np.polyfit(x, y, 1)
        f_lin = np.poly1d(params)
        t_refill = mdates.num2date(f_lin(25))
        str_refill = t_refill.strftime("%H:%M:%S")

    # update the plot
    if plot_data_L1 == None:
        plot_data_L1, = plt.plot([mdates.num2date(new_time), datetime.now()], [new_value_L1, new_value_L1], c='b', label='L1Level_MON')
        plot_data_L2, = plt.plot([mdates.num2date(new_time), datetime.now()], [new_value_L2, new_value_L2], c='g', label='L2Level_MON')
        plt.legend()
    else:
        plot_data_L1.set_xdata(mdates.num2date(times))
        plot_data_L1.set_ydata(values_L1)
        plot_data_L2.set_xdata(mdates.num2date(times))
        plot_data_L2.set_ydata(values_L2)
        fig.canvas.draw()
        fig.canvas.flush_events()
        ax.set_xlim(times[0],times[-1])

    # update the figure
    fig.suptitle(f'current mono L2 level: {new_value_L2:.1f}%\nestimated refill time: {str_refill}', fontsize=18)
    fig.canvas.start_event_loop(.01)

    # wait a bit before asking for the next data point
    # waiting time depends on the number of data points in the buffer
    if len(times)<=1: 
        time.sleep(0.1)
    elif len(times)<=100: 
        time.sleep(0.3)
    else: 
        time.sleep(1.0)