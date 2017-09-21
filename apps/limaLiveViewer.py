import PyTango
import time
import matplotlib.pyplot as plt
import numpy as np
plt.ion()

# set up the lima proxy
limaPath = 'lima/limaccd/b-nanomax-mobile-ipc-01'
lima = PyTango.DeviceProxy(limaPath)

# learn about the shape and bit depth of the image
ignore, bytes, w, h = lima.image_sizes
dtype = {1: np.int8, 2: np.int16, 4:np.int32}[bytes]

# get images and plot them
while True:
    last = lima.last_image_ready
    if last > -1:
        print "trying to grab image %d" % last
        try:
            image = np.frombuffer(lima.getImage(last), dtype=dtype)
            image = image.reshape((h, w))
            print "   got it! min=%d, max=%d"%(image.min(), image.max())
            plt.imshow(image, vmin=0, vmax=3, interpolation='none')
            plt.draw()
        except:
            print "   something went wrong in this iteration, continuing"
    plt.pause(.1)


