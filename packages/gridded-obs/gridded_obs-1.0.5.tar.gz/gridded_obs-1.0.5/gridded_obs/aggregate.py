
import dask
@dask.delayed
def dask_verify(*args, **kwargs):
    return verify(*args, **kwargs)

def twod_stats(domain, params):
    """aggregate data for 2D stats
    """

    import datetime
    import warnings
    import numpy as np
    import gridded_obs.sql
    import sqlite3
    import time
    import gridded_obs.plot

    #list of indices to average in each averaging windows
    if len(params.leadtime_list) == 1:
        #only one leadtime has been verified this is what we use for twod stats
        twod_avg_list = [(0,)]
    else:
        this_lt = params.leadtime_list[0]
        deltat = datetime.timedelta(seconds=params.twod_deltat*60.)
        twod_avg_list = []
        while this_lt < params.leadtime_list[-1]:
            lower_bound = this_lt
            upper_bound = this_lt + deltat
            bool_list = [ lt >= lower_bound and lt < upper_bound for lt in params.leadtime_list]
            twod_avg_list.append(np.array(bool_list).nonzero()[0])
            this_lt += deltat

    #array of leadtime in minutes
    leadtime_minutes = np.array([ lt.days*1440. + lt.seconds/60. for lt in  params.leadtime_list], dtype=int)

    #each averaging window becomes a pannel
    n_windows = len(twod_avg_list)
    n_dates       = len(params.date_list)
    n_experiments = len(params.exp_list)

    print('')
    print('Aggregating 2D statististics')
    print(f'n_windows = {n_windows}')

    #in this loop, aggregation arrays are filled, data for each experiment 
    # are only averaged in the different averaging windows
    ref_bin_edges = None
    ref_dctpow_centers = None
    for kk, experiment in enumerate(params.exp_list):
        print(experiment, '   domain= ', domain)
        for jj, date in enumerate(params.date_list):

            sql_handler = gridded_obs.sql.Handler(date, params, verified_name=experiment)
            #print('reading data for '+experiment+str(date))
            conn = sql_handler.connect(none_for_nonexistent=True) 
            if conn is None:
                #file does not exists
                continue
            c = conn.cursor()

            if params.quantity is None:
                cmd = 'select quantity from info;'
                c.execute(cmd)
                params.quantity = c.fetchone()[0]


            #get histogram bin edges and make sure they are the same for all files being considered 
            if 'histograms' in params.twod_panels:
                hist_bin_edges = sql_handler.get_hist_bin_edges(c)
                if ref_bin_edges is None:
                    #
                    #this part of the code is run only once for first experiment and date being verified
                    #

                    #populate reference edges
                    ref_bin_edges = hist_bin_edges
                    #string that allows to read in histogram data
                    hist_string = sql_handler.strings_from_floats(ref_bin_edges, str_type='select')

                    #now that we know the dimension of histograms, we initialize result arrays
                    n_hist_bins = hist_bin_edges.size - 1
                    verified_hists  = np.full((n_experiments, n_windows, n_dates, n_hist_bins), np.nan)
                    reference_hists = np.full((               n_windows, n_dates, n_hist_bins), np.nan)

                else:
                    #this is run for every experiment and dates
                    if not np.allclose(ref_bin_edges, hist_bin_edges, equal_nan=True) :
                        raise ValueError('Problem: hist_bin_edges are not the same for all files encountered.')

            #get wavelenghts for average bands of cdt power and make sure they are the same in all files
            if 'dctpow' in params.twod_panels:
                dctpow_centers = sql_handler.get_dctpow_centers(c)
                if ref_dctpow_centers is None:
                    #
                    #this part of the code is run only once for first experiment and date being verified
                    #

                    #populate reference edges
                    ref_dctpow_centers = dctpow_centers
                    #string that allows to read in histogram data
                    dctpow_string = sql_handler.strings_from_floats(ref_dctpow_centers, str_type='select', remove_last=False)

                    #now that we know the dimension of dct_pow_centers we initialize result arrays
                    k_nbins = ref_dctpow_centers.size 
                    verified_dctpow  = np.full((n_experiments, n_windows, n_dates, k_nbins), np.nan)
                    reference_dctpow = np.full((               n_windows, n_dates, k_nbins), np.nan)

                else:
                    #this is run for every experiment and dates
                    if not np.allclose(ref_dctpow_centers, dctpow_centers, equal_nan=True) :
                        raise ValueError('Problem: dctpow_centers are not the same for all files encountered.')

            #domain id for this experiment and date
            domain_id = sql_handler.get_domain_id(c, domain)
            if domain_id is None:
                raise ValueError(f'Problem: getting domain_id for domain: {domain}')

            #average histogram for the different averaging windows
            for ii, lt_inds in enumerate(twod_avg_list):

                #for each leadtime in window
                window_size = len(lt_inds)
                if 'histograms' in params.twod_panels:
                    window_verified_hists   = np.full( (n_hist_bins, window_size), np.nan)
                    window_reference_hists  = np.full( (n_hist_bins, window_size), np.nan)
                if 'dctpow' in params.twod_panels:
                    window_verified_dctpow  = np.full( (k_nbins, window_size), np.nan)
                    window_reference_dctpow = np.full( (k_nbins, window_size), np.nan)

                #lead time that are part of this window
                for ee, lt_ind in enumerate(lt_inds):

                    #skip force certain leadtimes (leave values to NaN) if the user wants this
                    if np.any(lt_ind == params.leadtime_ignore_inds):
                        continue

                    if 'histograms' in params.twod_panels:
                        verified_hist_vals  = sql_handler.get_hist_values(c, 'hist_verified', leadtime_minutes[lt_ind], 
                                                                             domain_id, hist_bin_edges, hist_string)
                        reference_hist_vals = sql_handler.get_hist_values(c, 'hist_reference', leadtime_minutes[lt_ind], 
                                                                             domain_id, hist_bin_edges, hist_string)
                        if reference_hist_vals is None or verified_hist_vals is None :
                            pass
                        else:
                            window_verified_hists[:,ee]  = verified_hist_vals
                            window_reference_hists[:,ee] = reference_hist_vals


                    if 'dctpow' in params.twod_panels:
                        verified_dctpow_vals  = sql_handler.get_dctpow_values(c, 'dctpow_verified', leadtime_minutes[lt_ind], 
                                                                                  domain_id, dctpow_centers, dctpow_string)
                        reference_dctpow_vals = sql_handler.get_dctpow_values(c, 'dctpow_reference', leadtime_minutes[lt_ind], 
                                                                                  domain_id, dctpow_centers, dctpow_string)
                        if reference_dctpow_vals is None or verified_dctpow_vals is None :
                            pass
                        else:
                            window_verified_dctpow[:,ee]  = verified_dctpow_vals
                            window_reference_dctpow[:,ee] = reference_dctpow_vals


                #record averaged histogram foor this window and experiment
                if 'histograms' in params.twod_panels:
                    with warnings.catch_warnings():
                        # avoid warning when there is nothing to average
                        warnings.simplefilter("ignore", category=RuntimeWarning)

                        verified_hists[kk, ii, jj, :] = np.nanmean(window_verified_hists, axis=1)
                        if kk == 0:
                            #reference for first experiment will be used, we assume same reference for all experiments
                            reference_hists[ii, jj, :] = np.nanmean(window_reference_hists, axis=1)

                #record averaged histogram foor this window and experiment
                if 'dctpow' in params.twod_panels:
                    with warnings.catch_warnings():
                        # avoid warning when there is nothing to average
                        warnings.simplefilter("ignore", category=RuntimeWarning)

                        verified_dctpow[kk, ii, jj, :] = np.nanmean(window_verified_dctpow, axis=1)
                        if kk == 0:
                            #reference for first experiment will be used, we assume same reference for all experiments
                            reference_dctpow[ii, jj, :] = np.nanmean(window_reference_dctpow, axis=1)

            #we are done with this sql file
            conn.close()

    #
    #
    #Here, we make sure that what shows up as NaN in one experiment gets set to Nan in all experiments
    if params.make_same:
        #Make NaN in one experiment NaN in all experiments
        #we flatten 3D arrays along the experiment direction (axis=0) to propagate where there are NaN in any experiment
        v_hist_nan   = np.logical_not(np.isfinite(np.sum(verified_hists, axis=0)))
        r_hist_nan   = np.logical_not(np.isfinite(reference_hists))
        hist_nan_inds = np.logical_or(v_hist_nan, r_hist_nan).nonzero()

        if 'dctpow' in params.twod_panels:
            r_dctpow_nan = np.logical_not(np.isfinite(reference_dctpow))
            v_dctpow_nan = np.logical_not(np.isfinite(np.sum(verified_dctpow, axis=0)))
            dctpow_nan_inds = np.logical_or(v_dctpow_nan, r_dctpow_nan).nonzero()

        #propagate NaNs 
        #an entry missing in one of experiment or reference is marked as missing for all experiments
        reference_hists[hist_nan_inds] = np.nan
        for kk, experiment in enumerate(params.exp_list):
            verified_hists[kk,:,:,:][hist_nan_inds] = np.nan

        if 'dctpow' in params.twod_panels:
            reference_dctpow[dctpow_nan_inds] = np.nan
            for kk, experiment in enumerate(params.exp_list):
                verified_dctpow[kk,:,:,:][dctpow_nan_inds] = np.nan


    #
    #
    #we average data for all experiments
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

        avg_reference_hists = np.nanmean(reference_hists, axis=1)
        avg_verified_hists  = np.nanmean(verified_hists, axis=2)

        if 'dctpow' in params.twod_panels:
            avg_reference_dctpow = np.nanmean(reference_dctpow, axis=1)
            avg_verified_dctpow  = np.nanmean(verified_dctpow, axis=2)
        else:
            ref_dctpow_centers   = None
            avg_reference_dctpow = None
            avg_verified_dctpow  = None

    #
    #
    #make figure
    gridded_obs.plot.twod_panels(params, domain, twod_avg_list, leadtime_minutes,
                                 hist_bin_edges, avg_reference_hists, avg_verified_hists, 
                                 ref_dctpow_centers, avg_reference_dctpow, avg_verified_dctpow)



def time_series(td, params):
    """aggregate data for time series
    """

    import warnings
    import numpy as np
    import gridded_obs.sql
    import sqlite3
    import time
    import gridded_obs.plot

    #threshold and domain verified in this functions call
    threshold = td[0]
    domain = td[1]

    #dimension of aggregation array
    n_leadtimes   = len(params.leadtime_list)
    n_dates       = len(params.date_list)
    n_experiments = len(params.exp_list)

    #initialize aggregation arrays
    dims = (n_leadtimes, n_dates, n_experiments)
    x             = np.full(dims, np.nan)
    y             = np.full(dims, np.nan)
    z             = np.full(dims, np.nan)
    w             = np.full(dims, np.nan)
    lmin          = np.full(dims, np.nan)
    corr_coeff    = np.full(dims, np.nan)

    #fill aggregation arrays
    for kk, experiment in enumerate(params.exp_list):
        print('')
        print(experiment, '   threshold= ',threshold, '   domain= ', domain)
        for jj, date in enumerate(params.date_list):
            sql_handler = gridded_obs.sql.Handler(date, params, verified_name=experiment)
            #print('reading data for '+experiment+str(date))
            conn = sql_handler.connect(none_for_nonexistent=True) 
            if conn is None:
                warnings.warn('No sql file for date:'+str(date))
                continue
            c = conn.cursor()
            c.row_factory = sqlite3.Row
            domain_id = sql_handler.get_domain_id(c, domain)
            if domain_id is None :
                continue
            threshold_id = sql_handler.get_threshold_id(c, threshold)
            if threshold_id is None:
                continue
            cmd = '''select leadtime_minutes, x, y, z, w, lmin, corr_coeff
                                              from stats where (domain_id    = '''+str(domain_id)+''' and 
                                                                threshold_id = '''+str(threshold_id)+''' ) ;''' 
            c.execute(cmd)
            entries = c.fetchall()
            conn.close()

            if len(entries) == 0:
                warnings.warn('No entries for date:'+str(date))

            for entry in entries:
                #leadtime index
                if (( entry['leadtime_minutes'] >= params.leadtime_0) and 
                    ( entry['leadtime_minutes'] <=  params.leadtime_f) ) :
                    ii = int((entry['leadtime_minutes'] - params.leadtime_0) / params.delta_leadtime)
                    x[ii,jj,kk]          = entry['x']
                    y[ii,jj,kk]          = entry['y']
                    z[ii,jj,kk]          = entry['z']
                    w[ii,jj,kk]          = entry['w']
                    lmin[ii,jj,kk]       = entry['lmin']
                    corr_coeff[ii,jj,kk] = entry['corr_coeff']

        #we use finite number of hits to identify experiment with no data whatsoever
        #this will cause everything else to be set to NaN
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            if np.isclose(np.nansum(x[:,:,kk]), 0.):
                raise RuntimeError('Experiment:'+experiment+' has no data at all. We stop here as this would cause everything else to be rejected.')

    if params.make_same:
        #Make NaN in one experiment NaN in all experiments
        #we flatten 3D arrays along the experiment direction (axis=2) to propagate where there are NaN in any experiment
        x_nan_inds          = np.logical_not(np.isfinite(np.sum(x,         axis=2))).nonzero()
        y_nan_inds          = np.logical_not(np.isfinite(np.sum(y,         axis=2))).nonzero()
        z_nan_inds          = np.logical_not(np.isfinite(np.sum(z,         axis=2))).nonzero()
        w_nan_inds          = np.logical_not(np.isfinite(np.sum(w,         axis=2))).nonzero()
        lmin_nan_inds       = np.logical_not(np.isfinite(np.sum(lmin,      axis=2))).nonzero()
        corr_coeff_nan_inds = np.logical_not(np.isfinite(np.sum(corr_coeff,axis=2))).nonzero()
        #mark missing for all experiments
        #an entry missing in one experiment is marked as missing for all experiments
        for kk, experiment in enumerate(params.exp_list):
            x[:,:,kk][x_nan_inds]                   = np.nan
            y[:,:,kk][y_nan_inds]                   = np.nan
            z[:,:,kk][z_nan_inds]                   = np.nan
            w[:,:,kk][w_nan_inds]                   = np.nan
            lmin[:,:,kk][lmin_nan_inds]             = np.nan
            corr_coeff[:,:,kk][corr_coeff_nan_inds] = np.nan

    #
    #
    #time_series
    #average statistics
    avg_dims = (n_leadtimes, n_experiments)
    avg_fbias         = np.full(avg_dims, np.nan)
    avg_pod           = np.full(avg_dims, np.nan)
    avg_far           = np.full(avg_dims, np.nan)
    avg_csi           = np.full(avg_dims, np.nan)
    avg_gss           = np.full(avg_dims, np.nan)
    avg_lmin          = np.full(avg_dims, np.nan)
    avg_corr_coeff    = np.full(avg_dims, np.nan)
    n_avg_contingency = np.full(avg_dims, np.nan)
    n_avg_lmin        = np.full(avg_dims, np.nan)
    n_avg_corr_coeff  = np.full(avg_dims, np.nan)
    #ignore warnings for /0 we can handle NaN later
    with np.errstate(divide='ignore', invalid='ignore'):
        for kk, experiment in enumerate(params.exp_list):
            #sum x, y, z, w
            x_sum = np.nansum(x[:,:,kk], axis=1)
            y_sum = np.nansum(y[:,:,kk], axis=1)
            z_sum = np.nansum(z[:,:,kk], axis=1)
            w_sum = np.nansum(w[:,:,kk], axis=1)

            #make sure numbers are the same for each category
            nx = np.nansum(np.isfinite(x[:,:,kk]), axis=1)
            ny = np.nansum(np.isfinite(y[:,:,kk]), axis=1)
            nz = np.nansum(np.isfinite(z[:,:,kk]), axis=1)
            nw = np.nansum(np.isfinite(w[:,:,kk]), axis=1)
            if np.sum(nx-ny) > 0. or  np.sum(nx-nz) > 0. or np.sum(nx-nw) > 0.:
                raise ValueError('Number of x,y,x,w being averaged is not the same...')
            else: 
                n_avg_contingency[:,kk] = nx

            avg_fbias[:,kk] =  (x_sum + z_sum)/(x_sum + y_sum)          #frequency bias                                                         a+b / a+c
            avg_pod[:,kk]   = x_sum / (x_sum + y_sum)                   #probability of detection  % of events that are forecasted                a / a+c
            avg_far[:,kk]   = z_sum/(x_sum + z_sum)                     #false alarm rate        (# of false alarms) / (# of predicted events)    b / a+b
            avg_csi[:,kk]   = x_sum/(x_sum+y_sum+z_sum)                 #critical sucess index    (# of hits) / (# of events  +  # of false alarm) a/ a+c+b
            c = (x_sum+y_sum)*(x_sum+z_sum)/(x_sum+y_sum+z_sum+w_sum)   #event frequency
            avg_gss[:,kk]   = (x_sum-c)/(x_sum-c+y_sum+z_sum)           #Gilbert skill score      # of correct forecasts in excess of those expected by chance 
                                                                        #       / # of cases when there was a threat that would not have been forecasted by chance
                                                                        # think about it as csi corrected by chance            
                                                                        
            #other scores are simply averaged
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)

                #lmin
                avg_lmin[:,kk]        = np.nanmean(lmin[:,:,kk], axis=1)
                n_avg_lmin[:,kk] = np.nansum(np.isfinite(lmin[:,:,kk]), axis=1)

                #corr coeff
                avg_corr_coeff[:,kk] = np.nanmean(corr_coeff[:,:,kk], axis=1)
                n_avg_corr_coeff[:,kk]  = np.nansum(np.isfinite(corr_coeff[:,:,kk]), axis=1)

            #force certain leadtimes to NaN if the user wants this
            if params.leadtime_ignore_inds is not None:
                lt_inds = params.leadtime_ignore_inds
                avg_fbias[lt_inds,kk]      = np.nan
                avg_pod[lt_inds,kk]        = np.nan
                avg_far[lt_inds,kk]        = np.nan
                avg_csi[lt_inds,kk]        = np.nan
                avg_gss[lt_inds,kk]        = np.nan
                avg_lmin[lt_inds,kk]       = np.nan
                avg_corr_coeff[lt_inds,kk] = np.nan

    score_dict = {'fbias':      avg_fbias,
                  'pod':        avg_pod,  
                  'far':        avg_far,  
                  'csi':        avg_csi,  
                  'gss':        avg_gss,  
                  'lmin':       avg_lmin,
                  'corr_coeff': avg_corr_coeff, 
                  #
                  'n_fbias':      n_avg_contingency,
                  'n_pod':        n_avg_contingency,
                  'n_far':        n_avg_contingency,
                  'n_csi':        n_avg_contingency,
                  'n_gss':        n_avg_contingency,
                  'n_lmin':       n_avg_lmin,
                  'n_corr_coeff': n_avg_corr_coeff }

    #plot average error statistics 
    gridded_obs.plot.time_series(params, threshold, domain, score_dict)


def aggregate():

    """launch aggregation of pre-computed scores

    Several experiment can be compared side by side

    Checks make sure that the same dataset and verification parameters were 
    used for each experiment being compared

    Two types of graphs are produced:
        - time series
        - 2d plot in time intervals

    In all cases special care is taken that the same observations be used for all experiments

    """

    import os
    import argparse
    import datetime
    import numpy as np
    import dask.distributed
    import gridded_obs.common
    import domutils.legs as legs
    import domutils._py_tools as py_tools

    #arguments for the verification
    parser = argparse.ArgumentParser(description="variables necessary for score aggregation", 
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
    parser.add_argument("--leadtime_ignore",       nargs="+",  required=False,  help="[minutes] list of leadtimes that will be set to NaN",
                                                   default=None)
    parser.add_argument("--leadtime_greyed_out",   nargs="+",type=float, required=False,  help="[minutes] min and max leadtime to be greyed out",
                                                   default=None)
    parser.add_argument("--make_same",             type=str, required=False, help="make NaN in one experiment NaN in all experiments", default=True)
    parser.add_argument("--show_obs_num",          type=str, required=False, help="Show number of fcsts considered at each lead time", default=True)

    parser.add_argument("--quantity",              type=str,  required=False, default=None, help="quantity being verified")

    #what are we to plot
    parser.add_argument("--time_series",   nargs="+",type=str,  required=False, default=None, help="quantities to plot, from the bottom up, in time_series figures")
    parser.add_argument("--twod_panels",   nargs="+",type=str,  required=False, default=None, help="quantities to plot, from the bottom up, in 2D figures")
    parser.add_argument("--twod_deltat",             type=float,required=False, default=60., help="[minutes] time interval for 2D figures")


    #yrange for figures to be plotted   if no arguments passed, range is automatic
    parser.add_argument("--ylim_fbias",      nargs="+", type=str,  required=False, help="min, max ;  yrange for fbias plots",      default=None)
    parser.add_argument("--ylim_pod",        nargs="+", type=str,  required=False, help="min, max ;  yrange for pod plots",        default=None)
    parser.add_argument("--ylim_far",        nargs="+", type=str,  required=False, help="min, max ;  yrange for far plots",        default=None)
    parser.add_argument("--ylim_csi",        nargs="+", type=str,  required=False, help="min, max ;  yrange for csi plots",        default=None)
    parser.add_argument("--ylim_lmin",       nargs="+", type=str,  required=False, help="min, max ;  yrange for lmin plots",       default=None)
    parser.add_argument("--ylim_corr_coeff", nargs="+", type=str,  required=False, help="min, max ;  yrange for corr_coeff plots", default=None)
    parser.add_argument("--ylim_dctpow",     nargs="+", type=str,  required=False, help="min, max ;  yrange for dct_spectra",      default=None)
    parser.add_argument("--ylim_hist",       nargs="+", type=str,  required=False, help="min, max ;  yrange for histograms",       default=None)

    #output locations
    parser.add_argument("--score_dir" ,              type=str,   required=True,  help="base directory where scores will be read.")
    parser.add_argument("--outname_file_struc",      type=str,   required=False,  help="File structure for output name; use '%%reference_name' and '%%verified_name' ", 
                        default='%%verified_name_vs_%%reference_name__%%Y%%m%%d%%H.sqlite3')
    parser.add_argument("--figure_dir" ,             type=str,   required=True,  help="directory where figures will be saved")
    parser.add_argument("--figure_format" ,          default='svg', type=str,   required=False,  help="format of output images")
    parser.add_argument("--verif_hash" ,             type=str,   required=False, default='abcdef',  help="verif hash to make sql handler happy")
    #parameters governing the aggregation
    parser.add_argument("--verif_domains", nargs="+",type=str,   required=True,  help="[imin,jmin,imax,jmax] bottom-left and top-right verificatoin domain ")
    parser.add_argument("--thresholds",    nargs="+",type=float, required=True,  help="list of thresholds to verify")

    parser.add_argument("--n_cpus",                  type=int,   required=True,  help="number of cpus for parallel execution set to 1 for serial execution")

    #parameters governing the experiments being verified
    parser.add_argument("--reference_name",          type=str,  required=True,  help="name of reference dataset for all experiments being compared")
    parser.add_argument("--exp_list",     nargs="+", type=str,  required=True,  help="list of experiments to plot")
    parser.add_argument("--exp_desc",     nargs="+", type=str,  required=True,  help="A more layman name for experiments 'LHN_off' for use in figure labels. ")
    parser.add_argument("--exp_color",    nargs="+", type=str,  required=False, default=None,  help="list of colors for each experiment see comment above")
    parser.add_argument("--exp_linestyle",nargs="+", type=str,  required=False, default=None,  help="matplotlib linestyle for each experiment")
    parser.add_argument("--exp_linewidth",nargs="+", type=float,required=False, default=None,  help="iatplotlib linewidth for each experiment")

    #parse arguments
    (params, unknown_args) = parser.parse_known_args()

    if len(unknown_args) > 0:
        print('unknown arguments:')
        print(unknown_args)

    #---------------------------------------------------------------------------

    #set variable to None if any values passed is a string = 'None'
    #also converts to numpy array of floats
    params.ylim_fbias      = gridded_obs.common.str2none(params.ylim_fbias,      desired_np_type=float)
    params.ylim_pod        = gridded_obs.common.str2none(params.ylim_pod,        desired_np_type=float)
    params.ylim_far        = gridded_obs.common.str2none(params.ylim_far,        desired_np_type=float)
    params.ylim_csi        = gridded_obs.common.str2none(params.ylim_csi,        desired_np_type=float)
    params.ylim_lmin       = gridded_obs.common.str2none(params.ylim_lmin,       desired_np_type=float)
    params.ylim_corr_coeff = gridded_obs.common.str2none(params.ylim_corr_coeff, desired_np_type=float)
    params.ylim_hist       = gridded_obs.common.str2none(params.ylim_hist,       desired_np_type=float)
    params.ylim_dctpow     = gridded_obs.common.str2none(params.ylim_dctpow,     desired_np_type=float)

    #convert strings to bool for certain variables
    params.make_same    = gridded_obs.common.str2bool(params.make_same)
    params.show_obs_num = gridded_obs.common.str2bool(params.show_obs_num)

    #initialize dask client if parallel execution is desired
    params.dask_client_exists = False
    if params.n_cpus > 1 :
        client = dask.distributed.Client(processes=True, threads_per_worker=1, n_workers=params.n_cpus, silence_logs=40)
        params.dask_client_exists = True

    #make sure delta_date is specified
    if params.date_f is not None:
        if params.delta_date is None:
            raise ValueError('argument "delta_date" must be specified when date_f is specified')

    #default if unspecified
    if params.exp_color is None:
        default_colors = ['l_blue_0.7','l_green_0.7','l_orange_0.7','l_red_0.7','l_pink_0.7','l_purple_0.7','l_yellow_0.7','l_brown_0.7']
        params.exp_color = default_colors[0:len(params.exp_list)]

    if params.exp_desc is None:
        params.exp_desc = params.exp_list

    if params.exp_linestyle is None:
        params.exp_linestyle = 'solid' * len(params.exp_list)

    if params.exp_linewidth is None:
        params.exp_linewidth = [10] * len(params.exp_list)

    #validate number of arguments

    if len(params.exp_desc) != len(params.exp_list):
        raise ValueError('exp_desc must have the same number of elements as exp_list')

    if len(params.exp_color) != len(params.exp_list):
        raise ValueError('exp_color must have the same number of elements as exp_list')

    if len(params.exp_linestyle) != len(params.exp_list):
        raise ValueError('exp_linestyle must have the same number of elements as exp_list')

    if len(params.exp_linewidth) != len(params.exp_list):
        raise ValueError('exp_linewidth must have the same number of elements as exp_list')

    #process colors into something that matplotlib will like
    for ii, input_color in enumerate(params.exp_color):
        if input_color[0] == '(' and input_color[-1] == ')':
            #we have (r,g,b) or (r,g,b,a)
            rgb_list = input_color[1:-1].split(',')
            if len(rgb_list) == 3:
                #we have (r,g,b) 
                params.exp_color[ii] = tuple(np.array([float(elem)/255. for elem in rgb_list]))
            if len(rgb_list) == 4:
                #we have (r,g,b,a) 
                rgb_arr = np.array([float(elem)/255. for elem in rgb_list])
                rgb_arr[-1] = float(rgb_list[-1])  #   alpha should not be divided by 255.
                params.exp_color[ii] = tuple(rgb_arr)
            else:
                raise ValueError("color '(r,g,b)' or '(r,g,b,a)' can only have 3 or 4 elements")
        elif input_color[0:2] == 'l_':
            #we have a legs color of type:  'l_orange_0.7'
            try:
                out = input_color[2:].split('_')
                #exception for b_w
                if out[0] == 'b' and out[1] == 'w':
                    color = 'b_w'
                    value = out[2]
                else:
                    color, value = out
            except:
                raise ValueError("conversion problem: legs color should be of the form 'l_orange_0.7")
            c_map = legs.PalObj(color_arr=color)
            rgb_arr = c_map.to_rgb(value)[0]/255.
            params.exp_color[ii] = tuple(rgb_arr)
        else:
            #in all other cases, the string present in params.exp_color will be passed directly to matplotlib
            pass

    #list of dates over which to iterate
    params.date_list = gridded_obs.common.make_date_list(params)

    #list of leadtimes (datetime.timedelta) that will be verified in parallel
    params.leadtime_list = gridded_obs.common.make_leadtime_list(params)

    #list of indexes of leadtime that should be ignored
    params.leadtime_ignore_inds = None
    if params.leadtime_ignore is not None:
        inds = []
        for leadtime_m in params.leadtime_ignore:
            #litteral None string
            if leadtime_m == 'None':
                params.leadtime_ignore_inds = None
                break

            leadtime_dt = datetime.timedelta(seconds=float(leadtime_m)*60.)
            ind = np.array([lt == leadtime_dt for lt in params.leadtime_list]).nonzero()[0][0]
            inds.append(ind)
        params.leadtime_ignore_inds = inds


    #
    #
    #make directory that will contain figures
    exps_dir = '_'.join(params.exp_list)+'_vs_'+params.reference_name
    date_dir =  params.date_list[0].strftime('%Y%m%d%H')+'_to_'+ params.date_list[-1].strftime('%Y%m%d%H')
    params.figure_dir = os.path.join(params.figure_dir, exps_dir, date_dir)
    py_tools.parallel_mkdir(params.figure_dir)

    #
    #
    #2D plots
    for domain in params.verif_domains:
        twod_stats(domain, params)

    #
    #
    #time series
    plot_time_series = True
    if len(params.time_series) == 1:
        if params.time_series[0] == 'None':
            #nothing asked for time series, skip
            plot_time_series = False
    if plot_time_series :
        td_list = [(threshold,domain) for threshold in params.thresholds for domain in params.verif_domains]
        for td in td_list:
            time_series(td, params)



if __name__ =='__main__':
    aggregate()
