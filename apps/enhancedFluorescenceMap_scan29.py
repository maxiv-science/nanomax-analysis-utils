import nmutils
import nmutils.utils.fmre
import matplotlib.pyplot as plt
import numpy as np

# Create an instance of a Scan subclass
myscan = nmutils.core.nanomaxScan_stepscan_april2017()

# Add data to the scan
myscan.addData(
    dataType='xrf', 
    filename="C:/nanomax_deconv/testing.h5", 
    scannr=29,
)

# CALL ENHANCEMENT ENGINES
# HERE I call all the different types

#### TOTAL VARIATION ####
EFM_TV,residuals_TV,info_TV = nmutils.utils.fmre.enhance(
    myscan, 
    'C:/nanomax_deconv/scan29_ePIE_EPIE_0990.ptyr', 
    lam=2e-6,
    roi='1 1300',
    method='TV',
    non_neg=False,
    iterations=30,
    interp_method='linear',#'None'#'nearest'
    slowdown=2.
    )

#### LANDWEBER ####
EFM_Landweber,residuals_Landweber,info_Landweber = nmutils.utils.fmre.enhance(
    myscan, 
    'C:/nanomax_deconv/scan29_ePIE_EPIE_0990.ptyr', 
    lam=.9,
    roi='1 1300',
    method='Landweber',
    non_neg=True,
    iterations=20,
    interp_method='linear'
    )

#### TIKHONOV ####
EFM_Tik,residuals_Tik,info_Tik = nmutils.utils.fmre.enhance(
    myscan, 
    'C:/nanomax_deconv/scan29_ePIE_EPIE_0990.ptyr', 
    lam=1e-5,
    roi='1 1300',
    method='Tikhonov',
    non_neg=False,
    iterations=50,
    interp_method='linear',#'None'#'nearest'
    slowdown=2.
    )

#### CGLS ####
EFM_CGLS,residuals_CGLS,info_CGLS = nmutils.utils.fmre.enhance(
    myscan, 
    'C:/nanomax_deconv/scan29_ePIE_EPIE_0990.ptyr', 
    roi='1 1300',
    method='CGLS',
    non_neg=False,
    iterations=20,
    interp_method='linear',#'None'#'nearest'
    slowdown=2.
    )

fig1=plt.figure()
asize=64
ax1=fig1.add_subplot(221)
ax2=fig1.add_subplot(222)
ax3=fig1.add_subplot(223)
ax4=fig1.add_subplot(224)
ax1.imshow(EFM_Landweber[asize:-asize,asize:-asize])
ax2.imshow(EFM_TV[asize:-asize,asize:-asize])
ax3.imshow(EFM_Tik[asize:-asize,asize:-asize])
ax4.imshow(EFM_CGLS[asize:-asize,asize:-asize])

fig2=plt.figure()
ax1=fig2.add_subplot(211)
ax2=fig2.add_subplot(212)
ax1.imshow((np.angle(info_Landweber['Pty_obj'][asize:-asize,asize:-asize])))#FLIP PTYPY ARRAY
ax2.imshow(info_Landweber['interpolated_map'])

