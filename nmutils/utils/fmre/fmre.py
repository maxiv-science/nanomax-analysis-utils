import numpy as np
import solvers
import data
import projectors

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
            'alternatives': ['CGLS', 'Landweber', 'Tikhonov', 'TV'], # list the possibilities here
            },
        'lam': {
            'value': .1,
            'doc': 'Weight coefficient for regularization terms',
            'type': float,
            },
        'iterations': {
            'value': 20,
            'doc': 'Number of refinement iterations',
            'type': int,
            }
    }

    # copy defaults and update with passed options
    opts = default_opts.copy()
    opts = scan._updateOpts(opts, **kwargs) # the Scan class happens to have a handy helper function

    # parse the options
    roi = map(int, opts['roi']['value'].strip().split()) if opts['roi']['value'] else None
    method = opts['method']['value']
    lam = opts['lam']['value']
    iterations = opts['iterations']['value']
    try:
        assert method in opts['method']['alternatives']
    except:
        raise RuntimeError('Invalid method specified! Options are: %s'%str(opts['method']['alternatives']))

    # calculate the integrated fluorescence
    if roi:
        xrf_integrated = np.sum(scan.data.values()[0][:, roi[0]:roi[1]], axis=1)
    else:
        xrf_integrated = np.sum(scan.data.values()[0], axis=1)

    # just testing the options parsing
    print roi
    print method
    print lam
    print iterations

    # Example of using a function from a submodule.
    # This is where the analysis should happen.
    solvers.dummy()


    result = np.random.randint(0, 255, (5,5))
    info = "this is convergence info"
    return result, info
