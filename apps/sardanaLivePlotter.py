import PyTango
import numpy as np
import time
import argparse
import matplotlib.pyplot as plt
plt.ion()


class dataGrabber():
    """
    Class which grabs and parses the Sardana output for plotting
    simple scans.
    """

    # a magic string used for identifying the header line
    MAGIC = '#Pt No'

    def __init__(self, door, xname, yname):
        self.x = None
        self.y = None
        self.xname = xname
        self.yname = yname
        self.door = door

    def update(self):
        # find column headers
        i = 0
        headerLineN = None

        try:
            for line in self.door.Output:
                if self.MAGIC in line:
                    headerLineN = i
                    headers = line.split()
                    headers = [self.MAGIC,] + headers[2:]
                    self.xaxis = self.xname if self.xname is not None else headers[1]
                    self.yaxis = self.yname if self.yname is not None else headers[-2]
                    xcol = headers.index(self.xaxis)
                    ycol = headers.index(self.yaxis)
                i += 1
        except:
            return False

        if headerLineN is None:
            return False

        # get data
        data = [line.split() for line in self.door.Output[headerLineN+1:]]
        data = np.array(data)
        try:
            assert data.shape[0] > 1
            self.x, self.y = data[:, xcol], data[:, ycol]
            return True
        except:
            return False


if __name__ == '__main__':

    # parsing arguments
    parser = argparse.ArgumentParser(
        description='Live plotting of Sardana output. By default plots the second-last column (usually a channel) vs. the second column (usually a motor).',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--xaxis', type=str, dest='xaxis',
                        default=None,
                        help='the channel/motor to plot on the x axis')
    parser.add_argument('--yaxis', type=str, dest='yaxis',
                        default=None,
                        help='the channel/motor to plot on the y axis')
    parser.add_argument('--door', type=str, dest='door',
                        default='NanomaxExpert/DOOR/01',
                        help='The Sardana door to use')
    args = parser.parse_args()

    # make a door and a dataGrabber instance
    door = PyTango.DeviceProxy(args.door)
    grabber = dataGrabber(door, args.xaxis, args.yaxis)

    # plot in a loop
    while True:
        if grabber.update():
            print 'found %s data points' % grabber.x.shape
            plt.gca().clear()
            plt.plot(grabber.x, grabber.y, 'x-')
            plt.xlabel(grabber.xaxis)
            plt.ylabel(grabber.yaxis)
            plt.draw()
        else:
            print 'no data just now'
        plt.pause(1)

