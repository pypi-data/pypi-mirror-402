
"""functions common to verification and aggregation
"""

def make_date_list(params):
    """list of dates over which to iterate
    """

    import datetime
    import numpy as np

    if ((params.date_f == None) or
        (params.date_0 == params.date_f)):
        date_list = [params.date_0]
    else:
        t_diff = (params.date_f-params.date_0) + datetime.timedelta(seconds=1)    #+ 1 second for inclusive end point
        elasped_seconds = t_diff.days*3600.*24. + t_diff.seconds                  #I hate datetime objects
        delta_date_seconds = params.delta_date*60.
        date_list = [params.date_0 + datetime.timedelta(seconds=x) for x in np.arange(0,elasped_seconds,delta_date_seconds)]

    return date_list

def make_leadtime_list(params):
    """list of leadtimes (datetime.timedelta) that will be verified in parallel
    """

    import datetime
    import numpy as np

    if params.leadtime_0 == params.leadtime_f:
        leadtime_list = [datetime.timedelta(seconds=params.leadtime_0*60.)]
    else:
        small=1e-3
        leadtime_list = [datetime.timedelta(seconds=lt*60.) for lt in np.arange(params.leadtime_0,params.leadtime_f+small, params.delta_leadtime)]

    return leadtime_list

def str2bool(v):
    import argparse
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def str2none(v, desired_np_type=None):
    import numpy as np
    #is element or any elements in list are 'None', return None
    try:
        #will work for lists
        for elem in v:
            if elem is None:
               return None
            if elem.lower() in ('none'):
               return None
    except:
        #will work for single elements
        if v is None:
           return None
        if v.lower() in ('none'):
           return None
    if desired_np_type is None:
        return v
    else :
        return np.array(v, dtype=desired_np_type)
