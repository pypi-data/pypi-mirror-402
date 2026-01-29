
import dask

def _setup_logging(log_level=10, cwd=None, sub_dir=''):
    """setup logger and handlers

    Because of parallel execution, logging has to be setup for every forked processes
    so it is put in this reusable function

    log levels: 
        NOTSET=0
        DEBUG=10
        INFO=20
        WARN=30
        ERROR=40
        CRITICAL=50


    """

    import os
    import sys 
    import time
    from pathlib import Path
    import logging
    import domutils._py_tools as dpy
    import dask.distributed

    # logging is configured to write everything to stdout in addition to a log file
    # in a 'logs' directory
    logging_basename = 'verify'
    logger = logging.getLogger(logging_basename)

    if cwd is None:
        cwd = os.getcwd()+'/'

    # try to get worker id if there is one
    try:
        worker_id = dask.distributed.get_worker().id
        id_str = str(worker_id)
    except :
        worker_id=None
        id_str = ''

    #make sure 'logs' directory(ies) exist
    dpy.parallel_mkdir(cwd+'logs')
    if (worker_id is not None) and (sub_dir != ''):
        dpy.parallel_mkdir(cwd+'logs/'+sub_dir)

        worker_log_file = cwd+'logs/'+sub_dir+'/'+worker_id
        if not os.path.isfile(worker_log_file):
            # if worker log file does not already exist, existing loggers 
            # will refuse to create new files
            # we delete existing handlers here and new ones that work will get recreated below
            while logger.hasHandlers():
                logger.removeHandler(logger.handlers[0])

    # if this is a newly created logger, it will have no handlers
    # old handlers may also have been deleted above
    if not len(logger.handlers):

        logging.captureWarnings(True)
        logger.setLevel(log_level)
        #handlers
        stream_handler = logging.StreamHandler(sys.stdout)
        if worker_id is not None:
            file_handler = logging.FileHandler(cwd+'logs/'+sub_dir+'/'+worker_id, 'w')
        else:
            file_handler = logging.FileHandler(cwd+'logs/main.log', 'w')
        #levels
        stream_handler.setLevel(log_level)
        file_handler.setLevel(log_level)
        #format
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if worker_id is not None:
            stream_formatter = logging.Formatter(worker_id+' %(name)s -   %(message)s')
        else:
            stream_formatter = file_formatter
        stream_handler.setFormatter(stream_formatter)
        file_handler.setFormatter(file_formatter)
        #add handlers
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    return logger





@dask.delayed
def dask_verify_date(*args, **kwargs):
    return verify_date(*args, **kwargs)


def verify_date(params, date, leadtime):
    """ compute verifications scores between two gridded products
    
    """

    import os
    import time
    import datetime
    import warnings
    import gc
    import sqlite3
    import numpy as np
    from scipy import stats

    import gridded_obs.sql
    import gridded_obs.lmin_from_fss
    import gridded_obs.plot.compare_fields

    logger = _setup_logging(cwd=params.cwd, sub_dir='verify_date_log_dir')

    validity_date = date + leadtime
    leadtime_minutes = int(leadtime.days*1440. + leadtime.seconds/60.)
    logger.info(f'Starting : {date} at {leadtime_minutes}m for validity_date: {validity_date} ')

    #initialize sqlite file and object to interact with it
    sql_handler = gridded_obs.sql.Handler(date, params)

    read_data = True
    if params.complete_mode == 'complete':
        # we are trying to complete existing scores 
        if sql_handler.sqlite_file_exists() :
            # sqlite file exists, does it have entries for this leadtime?

            if sql_handler.found_entries_at_leadtime(leadtime_minutes):
                # entries exist in sqlite file at this leadtime, we will no try regenerating them
                read_data = False
            else:
                # this leadtime abscent from file, we will try to fill it
                read_data = True
        else:
            # sqlite files does not exists, read data and process scores
            read_data = True

    reference_dict = None
    verified_dict  = None
    if read_data:

        #read reference field
        reference_dict = params.reference_reader.get_data(date, leadtime)
        if reference_dict is None:
            logger.info('Reference dataset unavailable for: ' + str(date) + ' + ' + str(leadtime) + ' = ' + str(validity_date)
                         + ' Skipping this date')

        #read quantity being verified 
        verified_dict  =  params.verified_reader.get_data(date, leadtime)
        if verified_dict is None:
            logger.info('Verified dataset unavailable for: ' + str(date) + ' + ' + str(leadtime) + ' = ' + str(validity_date)
                         + ' Skipping this date')


    if (reference_dict is None) or (verified_dict is None):
        return np.array([0.],dtype=float)

    # if code gets here scores will be computed and saved

    #missing val
    missing = -9999.

    #data that will be pickled
    pickle_dict = {}

    #no quality => quality = 1 everywhere
    if reference_dict['qi_values'] is None:
        reference_dict['qi_values'] = np.ones_like(reference_dict['values'])


    all_bad = True
    for this_domain in params.verif_domains:
        logger.info(f'For domain: {this_domain}')

        pickle_dict[this_domain] = {}
        pickle_dict[this_domain]['leadtime_minutes'] = leadtime_minutes

        imin,jmin,imax,jmax = params.domain_dict[this_domain]
        #keep only data points in the verification domain
        verif_latitudes    =      reference_dict['lats'][imin:imax,jmin:jmax]
        verif_longitudes   =      reference_dict['lons'][imin:imax,jmin:jmax]
        verif_reference_pr =    reference_dict['values'][imin:imax,jmin:jmax]
        verif_reference_qi = reference_dict['qi_values'][imin:imax,jmin:jmax]
        verif_verified_pr  =     verified_dict['values'][imin:imax,jmin:jmax]

        #quality index < min_qi set to zero
        verif_reference_qi   = np.where(verif_reference_qi < params.min_qi,  0., verif_reference_qi)

        ##TODO leave commented!!! just for testing
        #verif_reference_qi   = np.where(verif_reference_qi < params.min_qi,  0., 1.)

        #make images showing what is being compared
        if params.img_dt > 0.:
            if np.isclose(np.mod(leadtime_minutes, params.img_dt), 0.) :
                gridded_obs.plot.compare_fields(verif_reference_pr, verif_reference_qi, verif_verified_pr, 
                                                verif_latitudes,    verif_longitudes,
                                                this_domain, params, date, leadtime)

        #list of points to be used for corr coeff calculations 
        good_pts = (verif_reference_qi >= params.min_qi).nonzero()
        if len(good_pts[0]) == 0:
            warnings.warn('All points in file have bad quality on domain'+this_domain+
                          ' and date: ' + str(date) + ' + ' + str(leadtime) + ' = ' + str(validity_date) + '  skipping.')
            continue

        # if code gets here, scores can be computed from at least some datapoints
        all_bad = False

        #list of points that will be set to zero for dct power spectra
        bad_pts = ((verif_reference_qi < params.min_qi) | np.isclose(verif_reference_pr, missing) | np.isclose(verif_verified_pr, missing)).nonzero()

        #
        #
        # histograms
        reference_hist, _ = np.histogram(verif_reference_pr, bins=params.hist_bin_edges, weights=verif_reference_qi)
        pickle_dict[this_domain]['reference_hist'] = reference_hist

        verified_hist, _ = np.histogram(verif_verified_pr, bins=params.hist_bin_edges, weights=verif_reference_qi)
        pickle_dict[this_domain]['verified_hist']  = verified_hist

        #
        #
        # DCT power spectrum
        #
        #reference data
        reference_pr_for_dct = np.copy(verif_reference_pr)
        if bad_pts[0].size > 0:
            reference_pr_for_dct[bad_pts] = 0.
        (reference_wavenum, 
         reference_wavelengths, 
         reference_power) = gridded_obs.pow_dct(reference_pr_for_dct, dx_km=params.grid_dx, n_bands=params.k_nbins)
        pickle_dict[this_domain]['reference_wavelengths']  = reference_wavelengths
        pickle_dict[this_domain]['reference_power']        = reference_power

        #
        #verified data
        verified_pr_for_dct = np.copy(verif_verified_pr)
        if bad_pts[0].size > 0:
            verified_pr_for_dct[bad_pts] = 0.
        (verified_wavenum, 
         verified_wavelengths, 
         verified_power) = gridded_obs.pow_dct(verified_pr_for_dct, dx_km=params.grid_dx, n_bands=params.k_nbins)
        pickle_dict[this_domain]['verified_wavelengths']  = verified_wavelengths
        pickle_dict[this_domain]['verified_power']        = verified_power


        for this_threshold in params.thresholds:
            th_string = f'th_{this_threshold}'
            pickle_dict[this_domain][th_string] = {}

            logger.info(f'verifying date: {date}, leadtime: {leadtime_minutes}, threshold: {this_threshold}')

            #apply threshold on quantity
            reference_true = np.where(verif_reference_pr >= this_threshold, 1., 0.)
            verified_true  = np.where(verif_verified_pr  >= this_threshold, 1., 0.)

            #
            #
            # contingency table ; data pointa are weighted by quality index of observation
            #   carefull here, reference is in the second column

            #hits (a)
            x = np.sum(verif_reference_qi * np.logical_and(np.isclose(verified_true,1.), np.isclose(reference_true,1.)))

            #misses (c)
            y = np.sum(verif_reference_qi * np.logical_and(np.isclose(verified_true,0.), np.isclose(reference_true,1.)))

            #false alarm (b)
            z = np.sum(verif_reference_qi * np.logical_and(np.isclose(verified_true,1.), np.isclose(reference_true,0.)))

            #zeros (d)
            w = np.sum(verif_reference_qi * np.logical_and(np.isclose(verified_true,0.), np.isclose(reference_true,0.)))

            pickle_dict[this_domain][th_string]['x'] = x
            pickle_dict[this_domain][th_string]['y'] = y
            pickle_dict[this_domain][th_string]['z'] = z
            pickle_dict[this_domain][th_string]['w'] = w

            #
            #
            # Pearson's correlation coefficient
            if len(good_pts[0]) < 10:
                #require at least 10 data points for computing correlation set to nan otherwise
                coff_coeff = np.nan
            else:
                reference_pts_for_corr = np.where(verif_reference_pr > this_threshold, verif_reference_pr, 0.)[good_pts]
                verified_pts_for_corr  = np.where(verif_verified_pr  > this_threshold, verif_verified_pr,  0.)[good_pts]

                corr_coeff, _ = stats.pearsonr(reference_pts_for_corr, verified_pts_for_corr)
            pickle_dict[this_domain][th_string]['corr_coeff'] = corr_coeff
            #
            #
            #minimum length scale for significant results using FSS in circular areas
            lmin_value = gridded_obs.lmin_from_fss(reference_true, verif_reference_qi, verified_true, 'fft',
                                                   params.lmin_range, grid_dx=params.grid_dx,
                                                   latitudes=verif_latitudes,   longitudes=verif_longitudes,
                                                   )
            pickle_dict[this_domain][th_string]['lmin_value'] = lmin_value

            ##for debugging
            #if lmin_value is None:
            #    #plot image
            #    gridded_obs.plot.compare_fields(reference_true, verif_reference_qi, verified_true, 
            #                                    verif_latitudes,   verif_longitudes,
            #                                    this_domain, params, validity_date, leadtime, threshold=this_threshold)


    #
    #
    #write stats to sqlite file 
    if not all_bad:
        sql_handler.sqlite_from_dict(params, pickle_dict, leadtime_minutes)
        logger.info(f'Data added to sqlite file date: {date}, leadtime: {leadtime_minutes}')


    #return something to maks dask happy
    return np.array([0.],dtype=float)



def forecast_loop(params):

    """
    When verifying data, one must loop over:

        - Validity date (T0)
        - Forecast lead time  (only applicable to forecasts, will be 0 when verifying an observation dataset against another)
        - members (only applicable to ensembles)
        - Thresholds
        - Verification domains

    This function is designed for verifying deterministic forecasts
    It loops over Validity dates and leadtimes, other  parameters are looped over in serial within the verify_date function

    args:
        - params see description in main

    """
    import os
    import glob
    import time
    import datetime
    import tempfile
    import numpy as np
    import dask.distributed
    import dask
    import dask.array as da
    #local
    import gridded_obs.sql 
    import gridded_obs.common

    logger = _setup_logging()
    logger.info('Starting forecast_loop')


    # clean pre-existing lock files from previous runs 
    for this_date in params.date_list:
        sql_handler = gridded_obs.sql.Handler(this_date, params)

        if os.path.isfile(sql_handler.date_lock_file):
            logger.info(f'removing old lockfile: {sql_handler.date_lock_file}')
            os.remove(sql_handler.date_lock_file)

        if (params.complete_mode == 'clobber') and os.path.isfile(sql_handler.sqlite_file):
            logger.info(f'Clobbering old sqlite file: {sql_handler.sqlite_file}')
            os.remove(sql_handler.sqlite_file)


    #iterate over forecast validity dates
    #execution on one interactive compute node 
    if params.n_cpus == 1:
        client = None

        #serial execution is executed here
        for date, leadtime in params.complete_date_list:
            out = verify_date(params, date, leadtime)

    else:
        client = None
        if params.scheduler_file is not None:
            #parallel executions with a previously started dask cluster that can be used via a schedule file
            client = dask.distributed.Client(scheduler_file=params.scheduler_file)

        else:
            #parallel execution with dask usin n_cpus
            logger.info(f'Creating local dask cluster with {params.n_cpus} cpus')
            client = dask.distributed.Client(processes=True, threads_per_worker=1, 
                                             n_workers=params.n_cpus, 
                                             local_directory=params.tmp_dir, 
                                             silence_logs=40) 

        #parallel execution is executed here
        if client is not None:

            #logger.info(str(client))
            # sample output so dask knows what to expect only shape and type matters here
            sample = np.array([0],dtype=float)  
            #list of desired outputs
            delayed_params = dask.delayed(params)
            res_list = []
            for date, leadtime in params.complete_date_list:
                res_list.append( da.from_delayed(dask_verify_date(delayed_params, date, leadtime), sample.shape, sample.dtype) )
            res_array = da.stack(res_list, axis=1)
            # expected result
            res = res_array.sum()
            # Computation is performed here
            t1 = time.time()
            total = res.compute()
            t2 = time.time()
            print('Scores computed in: ', t2-t1, 'seconds')

            client.close()


def verify():

    """launch verification


    Verification is performed between a "reference" and a "verified" datasets

    All arguments prefixed with '--reference_' will be passed directly to reader that must read the referece dataset
             "                  '--verified_'                     "

    gridded_obs does not care about what kind of data is being verified. 
    It is the user's responsability to make sure that the reference and verified readers 
    return quantities that are comparable (eg. with the same units).

    """

    import os
    import shutil
    import argparse
    import datetime
    import numpy as np
    import dask.distributed
    #local 
    import gridded_obs.readers 
    import gridded_obs.common

    #init proj obj
    import cartopy
    import domutils.geo_tools as geo_tools
    import domcmc.fst_tools as fst_tools


    # if logs directory exists, erase it and everything is contains
    if os.path.isdir('logs'):
        shutil.rmtree('logs')

    logger = _setup_logging()
    logger.info('Starting computation of atomic scores')

    #arguments for the verification
    parser = argparse.ArgumentParser(description="general variables necessary to all verifications", 
                                     prefix_chars='-+', formatter_class=argparse.RawDescriptionHelpFormatter)


    parser.add_argument("--date_0"  ,     type=lambda d: datetime.datetime.strptime(d, '%Y%m%d%H'),   
                                          required=True,  help=("[yyyymmddhh] (inclusive) first date being verified"))

    parser.add_argument("--date_f"  ,     type=lambda d: datetime.datetime.strptime(d, '%Y%m%d%H'),   
                                          required=False, help=("[yyyymmddhh] (inclusive) last date being verified"), 
                                          default=None)

    parser.add_argument("--delta_date",            type=float, required=False,  help="[minutes] interval between dates being verified",
                                                   default=None)

    parser.add_argument("--leadtime_0" ,           type=float, required=False,  help="[minutes] (inclusive) first leadtime to verify ",
                                                   default=0)
    parser.add_argument("--leadtime_f" ,           type=float, required=False,  help="[minutes] (inclusive) last  leadtime to verify ",
                                                   default=0)
    parser.add_argument("--delta_leadtime",        type=float, required=False, help="[minutes] interval between lead times being verified",
                                                   default=None)
    parser.add_argument("--grid_dx"    ,           type=float, required=True,  help="[km] size of grid tile")
    #output locations
    parser.add_argument("--outname_file_struc",    type=str,   required=False,  help="File structure for output name; use '%%reference_name' and '%%verified_name' ", 
                                                   default='%%verified_name_vs_%%reference_name__%%Y%%m%%d%%H.sqlite3')
    parser.add_argument("--score_dir" ,            type=str,   required=True,  help="directory where scores will be saved for aggregation later")

    parser.add_argument("--figure_dir" ,           type=str,   required=True,  help="directory where figures will be saved")
    parser.add_argument("--ylim_dctpow",nargs="+", type=float, required=False, help="min, max ;  yrange for dct_spectra",      default=None)
    parser.add_argument("--ylim_hist",  nargs="+", type=float, required=False, help="min, max ;  yrange for histograms",       default=None)
    parser.add_argument("--tmp_dir" ,              default='', type=str,   required=False, help="Large temporary directory")
    #parameters governing the verification itself
    parser.add_argument("--img_dt",                type=float, required=True,  help="[minutes] frequency at which figures will be generated  set to 0 for no figures")
    parser.add_argument("--verif_domains",nargs="+",type=str,  required=True,  help="[imin,jmin,imax,jmax] bottom-left and top-right verificatoin domain ")
    parser.add_argument("--thresholds",  nargs="+",type=float, required=True,  help="list of thresholds to verify")
    parser.add_argument("--k_nbins",               type=int,   required=True,  help="Number of bins for DCT spectra")
    parser.add_argument("--min_qi",                type=float, required=True,  help="Minimum quality index to consider for all verification")
    parser.add_argument("--hist_nbins",            type=int,   required=True,  help="Number of bins for histograms")
    parser.add_argument("--hist_min",              type=float, required=True,  help="[in unit being verified] minimum value for histograms ")
    parser.add_argument("--hist_max",              type=float, required=True,  help="[in unit being verified] maximum value for histograms ")
    parser.add_argument("--hist_log_scale",        type=str,   required=True,  help="set to True to use logscale in histograms ")
    parser.add_argument("--lmin_range",  nargs="+",type=float, required=False, help="minimum and maximum [km] radius for searching lmin ")
    parser.add_argument("--n_cpus",                type=int,   default=None, required=False, help="number of cpus for parallel execution set to 1 for serial execution")
    parser.add_argument("--scheduler_file",        type=str,   default='nothing', 
                                                               required=False, help="File allowing to connect to existing dask cluster")
    parser.add_argument("--complete_mode",         type=str,   required=False, default='clobber', help="'complete' or 'clobber' existing sql files")

    parser.add_argument("--verification_grid_file",type=str,   required=False, help="Standard file containing grid definition, if not provided, we use reference grid")
    parser.add_argument("--verification_grid_var" ,type=str,   required=False, help="Name of variable in verification_grid_file")
    parser.add_argument("--quantity",              type=str,   required=True,  help="quantity/field being verified")
    parser.add_argument("--accum_dt",              type=float, required=False, default=None, help="Length of accumulation in minutes")

    #parse arguments
    (params, unknown_args) = parser.parse_known_args()

    logger.info('')
    logger.info('General input parameters:')
    for key, value in params.__dict__.items():
        logger.info(f'{key}, {value}')

    logger.info('')
    logger.info('Input parameters related to data readers:')
    for value in unknown_args:
        logger.info(f'{value}')

    # add working directory to parameters, if may differ for dask workers
    params.cwd = os.getcwd()+'/'

    #
    #
    #process params
    if params.tmp_dir == '':
        params.tmp_dir = os.environ['BIG_TMPDIR']

    if params.scheduler_file == 'nothing':
        params.scheduler_file = None
    else:
        if not os.path.isfile(params.scheduler_file):
            raise ValueError(f'Scheduler file: {params.scheduler_file} does not exist.')

    #convert strings to bool for certain variables
    params.hist_log_scale = gridded_obs.common.str2bool(params.hist_log_scale)

    #compute edges of histograms
    if params.hist_log_scale:
        params.hist_bin_edges = np.geomspace(params.hist_min, params.hist_max, num=params.hist_nbins+1, endpoint=True)
    else:
        params.hist_bin_edges =  np.linspace(params.hist_min, params.hist_max, num=params.hist_nbins+1, endpoint=True)

    #
    #
    #make date and leadtime lists
    if params.date_f is not None:
        if params.delta_date is None:
            raise ValueError('argument "delta_date" must be specified when date_f is specified')
    #list of dates over which to iterate
    params.date_list = gridded_obs.common.make_date_list(params)
    #list of leadtimes (datetime.timedelta) that will be verified 
    params.leadtime_list = gridded_obs.common.make_leadtime_list(params)
    #one to unite them all
    params.complete_date_list = [(this_date, this_lt) for this_date in params.date_list for this_lt in params.leadtime_list]
    print(f'There are {len(params.complete_date_list)} dates+leadtime to verify')

    #
    #
    #add quantity to both readers
    for vr in ['reference', 'verified']:

        unknown_args.append(f'--{vr}_quantity')
        unknown_args.append(params.quantity)

        if params.quantity == 'accumulation':
            if params.accum_dt is not None:
                unknown_args.append(f'--{vr}_accum_dt')
                unknown_args.append(f'{params.accum_dt}')   #argparse argument are all strings
            else:
                raise ValueError('Agrument "accum_dt" must be specified when quantity is "accumulation"')

    #
    #
    #initialize readers for reference data and verified data
    params.reference_reader = gridded_obs.readers.reader_init('reference', unknown_args)
    params.verified_reader  = gridded_obs.readers.reader_init('verified',  unknown_args)
 
    #
    #
    #complete figure_name
    params.figure_dir = params.figure_dir.replace('%verified_name', params.verified_reader.name).replace('%reference_name', params.reference_reader.name)

    #
    #
    #Setting up the common grid for verification
    if params.verification_grid_file is not None:
        #Externally provided verificaton grid
        verif_grid_dict = fst_tools.get_data(file_name = params.verification_grid_file, 
                                             var_name  = params.verification_grid_var, 
                                             latlon=True)
        verification_grid_lats = verif_grid_dict['lat']
        verification_grid_lons = verif_grid_dict['lon']
    else:
        #default is to use the reference grid 
        for this_date, this_lt in params.complete_date_list:
            reference_dict = params.reference_reader.get_data(this_date, this_lt)
            if reference_dict is not None:
                break
        if reference_dict is None:
            raise ValueError('No reference fields valid in period...')
        verification_grid_lats = reference_dict['lats']
        verification_grid_lons = reference_dict['lons']

    #
    #
    # Determine if reference reader needs to perform interpolation
    for this_date, this_lt in params.complete_date_list:
        reference_dict = params.reference_reader.get_data(this_date, this_lt)
        if reference_dict is not None:
            break
    if reference_dict is None:
        raise ValueError('No reference fields valid in period...')
    reference_lats = reference_dict['lats']
    reference_lons = reference_dict['lons']
    if ( (reference_lats.shape != verification_grid_lats.shape)
         or not (    np.allclose(reference_lats, verification_grid_lats) 
                 and np.allclose(reference_lons, verification_grid_lons) )
        ):
        # interpolation options (say smoothing_radius) need to be specified in the calling script
        logger.info('Reference reader will perform interpolation')
        params.reference_reader.interp_init(reference_lats, reference_lons, 
                                            verification_grid_lats, verification_grid_lons)
    else:
        logger.info('Reference outputs are already on verification grid')

    #
    #
    # Determine if verified reader needs to perform interpolation
    for this_date, this_lt in params.complete_date_list:
        verified_dict = params.verified_reader.get_data(this_date, this_lt)
        if verified_dict is not None:
            break
    if verified_dict is None:
        raise ValueError('No verified fields valid in period...')
    verified_lats = verified_dict['lats']
    verified_lons = verified_dict['lons']
    if ( (verified_lats.shape != verification_grid_lats.shape)
         or not (    np.allclose(verified_lats, verification_grid_lats) 
                 and np.allclose(verified_lons, verification_grid_lons) )
       ):
        logger.info('Verified reader will perform interpolation')
        # interpolation options (say smoothing_radius) need to be specified in the calling script
        params.verified_reader.interp_init(verified_lats, verified_lons, 
                                           verification_grid_lats, verification_grid_lons)
    else:
        logger.info('Verified outputs are already on verification grid')

    #TODO 
    #find out a way to pass multiple domains through arguments
    #some shapefile magic should happen here as well
    #
    #                             imin jmin imax  jmax
    domain_dict = { 'radar2p5km':[230,  50,  2300, 700], 
                    'radar4km':  [125,  20,  1425, 490],
                    'rockies':   [125,  310, 500, 710],
                    'all':       [ 10,  10,  290, 290],
                    'yin':       [ 850, 75, 1300, 525],
                    'radar10km': [400,  200, 900,  550] }

    params.domain_dict = {}
    for this_domain in params.verif_domains:
        params.domain_dict[this_domain] = domain_dict[this_domain]


    if params.img_dt > 0.:
        #make projection objects for images

        #dictionaries with values for each domain
        params.crs = {}
        params.extent = {}
        params.proj_inds = {}
        params.ratio = {}
        for this_domain in params.verif_domains:
            logger.info(f'making figures proj_inds for domain: {this_domain}')

            imin,jmin,imax,jmax = params.domain_dict[this_domain]
            #keep only data points in the verification domain
            croped_latitudes  = verification_grid_lats[imin:imax,jmin:jmax]
            croped_longitudes = verification_grid_lons[imin:imax,jmin:jmax]
            logger.info(f'verification grid dim:{verification_grid_lats.shape}, cropping to {imin}:{imax},{jmin}:{jmax} for shape:{croped_latitudes.shape}')

            #if this_domain == 'radar2p5km':
            # Full national grid
            ratio  = 0.4
            pole_latitude=35.7
            pole_longitude=65.5
            lat_0 = 44.8 
            delta_lat = 4.6
            lon_0 = 266.1
            delta_lon = 34.1
            extent_latlon = [lon_0-delta_lon, lon_0+delta_lon, lat_0-delta_lat, lat_0+delta_lat]  
            crs = cartopy.crs.RotatedPole(pole_latitude=pole_latitude, pole_longitude=pole_longitude)

            #elif this_domain == 'yin':
            #    ratio  = 1.
            #    # Globe
            #    crs = cartopy.crs.Orthographic(central_longitude=-118.0, central_latitude=55.0, globe=None)
            #    extent_latlon=None

            ## Full baltrad radar grid
            #ratio = 0.5
            #pole_latitude = 35.7
            #pole_longitude = 65.5
            #lat_0 = 46.5
            #delta_lat = 23.
            #lon_0 = 254.50
            #delta_lon = 33.3
            #extent_latlon = [lon_0 - delta_lon, lon_0 + delta_lon, lat_0 - delta_lat, lat_0 + delta_lat]
            #crs = cartopy.crs.RotatedPole(pole_latitude=pole_latitude, pole_longitude=pole_longitude)

            ## HRDPS West
            #ratio = 0.888
            #pole_latitude=35.7
            #pole_longitude=87.0
            #lat_0 = 53.25
            #delta_lat = 3.83
            #lon_0 = -120.82
            #delta_lon = 8.5
            #extent_latlon=[lon_0-delta_lon, lon_0+delta_lon, lat_0-delta_lat, lat_0+delta_lat]  
            #crs = cartopy.crs.RotatedPole(pole_latitude=pole_latitude, pole_longitude=pole_longitude)
            

            #pixel resolution of image being generated
            grid_w_pts = 800
            image_res = [grid_w_pts,int(ratio*grid_w_pts)]

            #instantiate objects to handle geographical projection of data 
            proj_inds = geo_tools.ProjInds(src_lon=croped_longitudes, src_lat=croped_latitudes,
                                           dest_crs=crs, extent=extent_latlon,
                                           image_res=image_res)

            params.ratio[this_domain] = ratio
            params.crs[this_domain] = crs
            params.extent[this_domain] = proj_inds.rotated_extent
            params.proj_inds[this_domain] = proj_inds
            print('done')

    #launch verification
    forecast_loop(params)



if __name__ =='__main__':
    verify()
