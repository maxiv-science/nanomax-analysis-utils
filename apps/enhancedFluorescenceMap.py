import nmutils
import nmutils.utils.fmre
import matplotlib.pyplot as plt

# Create an instance of a Scan subclass
myscan = nmutils.core.nanomaxScan_stepscan_april2017()

# Add data to the scan
myscan.addData(
    dataType='xrf', 
    filename='/home/alex/bulk0-staff-nanomax/com20170517_eh3/testing/testing.h5', 
    scannr=17,
)

# Call the enhancement engine
image, info = nmutils.utils.fmre.enhance(
    myscan, 
    'some_file.ptyr', 
    lam=.2, )

# Plot the image
plt.imshow(image, interpolation='none')
plt.show()
