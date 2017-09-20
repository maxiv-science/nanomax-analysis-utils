import numpy as np
import solvers
import data
import projectors
import h5py
import nmutils
# Any functions/classes in this file are available globally as
# nmutils.utils.fmre.something()

def enhance(scan, ptyr_file, **kwargs):
    """
    Wrapper function which enhances a fluorescence map from a Scan
    object, using a retrieved probe from ptypy. Uses the first data 
    entry of the passed scan.

    Returns: An enhanced image, and refinement information.
    """

    # This is a complicated way of doing keyword arguments, but for GUI
    # applications it's handy because the GUI can learn what options to
    # expect, the doc strings for each, and whether to make a text box,
    # check box, drop down menu, etc.
    default_opts = {
        'roi': {
            'value': None,
            'doc': 'energy range to average over, in channel units',
            'type': str,
            },
        'method': {
            'value': 'Landweber',
            'doc': 'Optimization algorithm',
            'type': str,
            'alternatives': ['CGLS', 'Landweber', 'Tikhonov', 'TV','SIRT'], # list the possibilities here
            },
        'lam': {
            'value': .9,
            'doc': 'Weight coefficient for regularization terms',
            'type': float,
            },
        'iterations': {
            'value': 20,
            'doc': 'Number of refinement iterations',
            'type': int,
            },
        'non_neg': {
                'value':True,
                'doc': 'Non-negativity constraint for the EFM',
                'type': bool,
            },
        'slowdown': {
                'value':2,
                'doc': 'Factor to decrease step size in Conjugate Gradient Method',
                'type': float,
                },
        'show': {
                'value':True,
                'doc': "Turn image at each iteration on/off",
                'type': bool,
                        },
        'interp_method': {
                'value':'linear',
                'doc': "Interpolation method for backward operator",
                'type': str,
                'alternatives': ['nearest','linear','cubic','None'],
                },
        'propagate': {
                'value':0.,
                'doc': "Distance (in meters) to propagate probe function",
                'type': float,
                }
    }

    # COPY DEFAULT AND UPDATE WITH PASSED OPTIONS
    opts = default_opts.copy()
    opts = scan._updateOpts(opts, **kwargs) # the Scan class happens to have a handy helper function


    #CHECK METHODS VALIDITY
    try:
        assert opts['method']['value'].lower() in [s.lower() for s in opts['method']['alternatives']]
    except:
        raise RuntimeError('Invalid method specified! Options are: %s'%str(opts['method']['alternatives']))
    #Check valid interpolation method
    try:
        assert opts['interp_method']['value'] in opts['interp_method']['alternatives']
    except:
        raise RuntimeError('Invalid Interpolation method specified! Options are: %s'%str(opts['interp_method']['alternatives']))
    
    # IMOPRT PROBE ARRAY AND PIXEL SIZE FROM PTYPY RECONSTRUCTION
    with h5py.File(ptyr_file, 'r') as hf:
        probe = np.array(hf.get('content/probe/S00G00/data'))[0]
        probe=np.rot90(probe,2) #CONFIRM THIS SHIT _HERE!!!!! LOOKS OK COMPARING EFM WITH PHASE MAP
        psize = np.array(hf.get('content/probe/S00G00/_psize'))[0]
        obj = np.array(hf.get('content/obj/S00G00/data'))[0]
        obj=np.rot90(obj,2)
        energy=np.array(hf.get('content/probe/S00G00/_energy'))
    print "Loaded probe %d x %d"%(probe.shape)
    print "Pixel size = %.1f nm"%(psize*1e9)
    
    #PROPAGATE PROBE FUNCTION IF REQUIRED
    dx=opts['propagate']['value']
    if dx <>0:
        print "propagating probe by %d mum"% (dx*1e6)
        probe=np.squeeze(nmutils.utils.propagateNearfield(probe,psize,dx,energy))
 
        
        
    # PARSE OPTIONS AND DATA TO A SINGLE OBJECT 'dat'
    dat=data.Data()
    dat.roi = map(int, opts['roi']['value'].strip().split()) if opts['roi']['value'] else None
    dat.method = opts['method']['value']
    dat.reg_param = opts['lam']['value']
    dat.n_iter = opts['iterations']['value']
    dat.slowdown= opts['slowdown']['value']
    dat.interp_method=opts['interp_method']['value']
    dat.show=opts['show']['value']
    dat.x=scan.positions[:,0]*1e-6/psize #Convert scanning positions in microns to Pixels
    dat.y=scan.positions[:,1]*1e-6/psize
    dat.probe=np.square(np.abs(probe))
    dat.obj=obj


    # calculate the integrated fluorescence
    if dat.roi:
        dat.fluomap = np.sum(scan.data.values()[0][:, dat.roi[0]:dat.roi[1]], axis=1)
    else:
        dat.fluomap = np.sum(scan.data.values()[0], axis=1)
    
    
    # just testing the options parsing
    print "Fluorescence Spectra integrated from %d to %d"%(dat.roi[0],dat.roi[1])
    if dat.method=='SIRT' or dat.method == 'CGLS':
        print "Running %s method for %d iterations"%(dat.method, dat.n_iter)
    else:
        print "Running %s method with reg. parameter = %.4g for %d iterations"%(dat.method , dat.reg_param , dat.n_iter)

  
    
    if dat.method.lower() == 'landweber':
        solvers.landweber(dat)
    elif dat.method.lower() == 'sirt':
        solvers.SIRT(dat)
    else:
        solvers.CGM(dat)
    
    info={'roi':dat.roi,'method':dat.method,'iterations':len(dat.residuals),'Pty_obj':obj,'interpolated_map':dat.fluomap2d,'energy':energy,'a':probe}
    return dat.EFM, dat.residuals, info
