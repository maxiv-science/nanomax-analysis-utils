import numpy as np
from . import solvers
from . import data
from . import projectors

# Any functions/classes in this file are available globally as
# nmutils.utils.fmre.something()

DEFAULTS = {
    'roi': None,
    'method': 'CGM',
    'lam': .1,
    'iterations': 20,
}

def enhance(scan, ptyr_file, **kwargs):
    """
    Wrapper function which enhances a fluorescence map from a Scan
    object, using a retrieved probe from ptypy. Uses the first data 
    entry of the passed scan.

    Returns: An enhanced image, and refinement information.
    """

    # copy defaults and update with passed options
    opts = DEFAULTS.copy()
    opts.update(kwargs)
    print("Will use these options")
    print(opts)

    # extract all the options
    roi = opts['roi']
    method = opts['method']
    lam = opts['lam']
    iterations = opts['iterations']

    if roi:
        xrf_integrated = np.sum(list(scan.data.values())[0][:, roi[0]:roi[1]], axis=1)
    else:
        xrf_integrated = np.sum(list(scan.data.values())[0], axis=1)


    # Example of using a function from a submodule.
    # This is where the analysis should happen.
    solvers.dummy()


    result = np.random.randint(0, 255, (5,5))
    info = "this is convergence info"
    return result, info
