
#implementation of parallel FSS for Lmin in HRDPS in "resonable" time


    #np.set_printoptions(threshold=np.inf)

import dask
@dask.delayed
def dask_partial_fractions(*args, **kwargs):
    return partial_fractions(*args, **kwargs)

def partial_fractions(radius_km, 
                      this_batch, latitudes, longitudes,
                      kdtree, reference_true, reference_qi, verified_true, 
                      small=1e-3):

    """compute FSS fractions for reference and verified fields

    uses kdtree to find all neighbors within a given radius
    arguments:
        radius_km:      [km] radius of circle for computing FSS
        this_batch:     [1D ndarray] indices in lat/lon arrays to process 
        latitudes:      [1D ndarray] latitudes of grid for estimating fractions
        longitudes:     [1D ndarray] longitudes of grid for estimating fractions
        kdtree:         [object] kdtree object for finding data points with observations within a certain radius
        reference_true: [1D ndarray] observation precip rate > threshold    ;length of this array matches lat/lon used in building kdtree
        reference_qi:   [1D ndarray] observation quality index [0,1]        ;length of this array matches lat/lon used in building kdtree
        verified_true:  [1D ndarray] verified precip rate > threshold       ;length of this array matches lat/lon used in building kdtree
        small:          [float] values below which sum of quality index is considered zero
    """

    import time
    import numpy as np

    #convert lat/lon of points to search to xyz
    ii_s = this_batch[0,:]
    jj_s = this_batch[1,:]
    batch_xyz = to_xyz(longitudes[ii_s,jj_s], latitudes[ii_s,jj_s])

    #initialize output array
    reference_fractions = np.zeros_like(latitudes)
    verified_fractions  = np.zeros_like(latitudes)
    
    #list of neighboring points
    radius_m = 1e3*radius_km
    for ii, jj, xyz in zip(ii_s, jj_s, batch_xyz):
        #for some reason, calling kdtree outside the loop makes things slower...
        ball_list = kdtree.query_ball_point(xyz, radius_m)

        #record fractions
        if len(ball_list) == 0:
            #no valid datapoints
            reference_fractions[ii,jj] = -1.
            verified_fractions[ii,jj]  = -1.
        else:
            #generate fractions
            w_sum = np.sum(reference_qi[ball_list])
            #only normalize if sum of weights is larger than a small value. Otherwise, no data of sufficient quality was present
            if w_sum > small:
                reference_fractions[ii,jj] = np.sum(reference_qi[ball_list]*reference_true[ball_list]) / w_sum
                verified_fractions[ii,jj]  = np.sum(reference_qi[ball_list]* verified_true[ball_list]) / w_sum
            else:
                reference_fractions[ii,jj] = -1.
                verified_fractions[ii,jj]  = -1.

    return np.dstack((reference_fractions, verified_fractions))


def fss_diff(radius, target_fss, mode, 
             reference_true, reference_qi, verified_true, grid_dx,
             n_cpus=1, verif_longitudes=None, verif_latitudes=None,
             small = 1e-3, debug=False):

    """difference between FSS as a given radius and pre-computed FSS target

    This function is to be used by a minimizer to find smallest lenghtscale at which 
    a forecast is usefull

    Three "modes" or methods for computing FSS can be used
    - fft               by far the fastest; assumes regularly gridded data with a quality index
    - manual_parallel   Manual convolution performed in parallel; accepts irregularly gridded data defined by lat/lon
    - manual_serial     Manual convolution performed serially

    The three methods were verified to give the same FSS +- 0.01

    args:
    radius:                 [float km] radius of circle for computing FSS
    target_fss:             [float]    FSS value above which a forecast is deemed "skilled"
    mode:                   [str]      method to use for FSS computation; see above
    reference_true:         [2d ndarray] 1 where references values > threshold, 0 otherwise
    reference_qi:           [2d ndarray] quality index of reference data
    verified_true:          [2d ndarray] 1 where rverified values > threshold, 0 otherwise
    grid_dx:                [float km] size of grid tiles, assumed constant
    n_cpus:                 [int] only for method "manual_parallela; " number of cpus 
    verif_longitudes:       [ndarray] longitudes of verification grid
    verif_latitudes:        [ndarray] latitudes  of verification grid
    small:                  [float] value below which sum of quality index if considered zero
    debug:                  [bool] output fractions for debugging

    """

    import numpy as np
    import time
    import dask
    import dask.array as da
    import scipy.signal

    if not ((mode == 'fft') or (mode == 'manual_serial') or (mode == 'manual_parallel')) :
        raise ValueError('Unrecognized mode')

    if mode == 'fft':
        #weighted fractions through fft convolution

        #other possible kernels
        #   kernel = np.exp(-1.*np.sqrt(xx**2.+yy**2.)/.02)
        #   kernel = np.outer(scipy.signal.windows.gaussian(npts, 3), scipy.signal.windows.gaussian(npts, 3))
        #
        #making uniform circular kernel
        npts = int(2.*(radius/grid_dx)+1.)
        xx, yy = np.meshgrid(np.linspace(-1.,1.,npts),np.linspace(-1.,1.,num=npts))
        kernel = np.where(np.sqrt(xx**2. + yy**2.) <= 1., 1., 0.)

        #convolve quality index
        qi_convol        = scipy.signal.fftconvolve(reference_qi,    kernel, mode='same')

        #qi_convol will be used as a denominator
        #these indices mark values that large enough to be used
        #also get rid of -ve values that occur due to noise in the convolution
        inds_f = (qi_convol > small).nonzero()

        #-ve values in output will not be used for FSS computation
        reference_fractions = np.full_like(qi_convol, -1.)  
        verified_fractions  = np.full_like(qi_convol, -1.)  

        #convolve and normalize
        #
        reference_pr_qi_convol = scipy.signal.fftconvolve(reference_true * reference_qi, kernel, mode='same') 
        reference_fractions[inds_f] = reference_pr_qi_convol[inds_f] / qi_convol[inds_f]
        #
        verified_pr_qi_convol  = scipy.signal.fftconvolve( verified_true * reference_qi, kernel, mode='same') 
        verified_fractions[inds_f]  = verified_pr_qi_convol[inds_f]  / qi_convol[inds_f]


    else:
        #sample everything where observations are valid
        #verification can only be performed in the presence of observations
        inds = np.asarray(reference_qi > 0.).nonzero()
        if inds[0].size == 0:
            warnings.warn('no observations with quality index greater than threshold in the verification domain. Returning lmin=NaN')
            return np.nan
        sampled_latitudes      =  verif_latitudes[inds]
        sampled_longitudes     = verif_longitudes[inds]
        sampled_reference_true =   reference_true[inds]
        sampled_reference_qi   =     reference_qi[inds]
        sampled_verified_true  =    verified_true[inds]
        orig_x = np.arange(0, verif_latitudes.shape[0])
        orig_y = np.arange(0, verif_latitudes.shape[1])
        orig_xx, orig_yy = np.meshgrid(orig_x,orig_y,indexing='ij')
        orig_inds = np.vstack((orig_xx.ravel(), orig_yy.ravel()))

        #build kdtree using all points that can be used in the verification
        grid_xyz = to_xyz(sampled_longitudes, sampled_latitudes)
        kdtree = scipy.spatial.cKDTree(grid_xyz, balanced_tree=False)

        #divide this list into chuncks that fit the number of processors we have for the job
        splitted_ij = np.array_split(orig_inds, n_cpus, axis=1)

        if mode == 'manual_serial':

            reference_fractions = np.zeros_like(verif_latitudes)
            verified_fractions =  np.zeros_like(verif_latitudes)
            for this_batch in splitted_ij:
                total = partial_fractions(radius, 
                                          this_batch, verif_latitudes, verif_longitudes, 
                                          kdtree, sampled_reference_true, sampled_reference_qi, sampled_verified_true)
                this_ref_frac   = total[:,:,0]
                this_verif_frac = total[:,:,1]
                reference_fractions += this_ref_frac
                verified_fractions  += this_verif_frac

        elif mode == 'manual_parallel':

            # sample output so dask knows what to expect only shape and type matters here
            sample = np.dstack((verif_latitudes, verif_longitudes))
            #list of desired outputs
            res_list = [da.from_delayed(dask_partial_fractions(radius, 
                                                               this_batch, verif_latitudes, verif_longitudes, 
                                                               kdtree, sampled_reference_true, sampled_reference_qi, sampled_verified_true), 
                                                               sample.shape, sample.dtype) for this_batch in splitted_ij]
            res_array = da.stack(res_list, axis=3)
            # expected result
            res = res_array.sum(axis=3)
            # Computation is performed here.
            total = res.compute()
            reference_fractions = total[:,:,0]
            verified_fractions  = total[:,:,1]



    #compute FSS
    #remove all -ve values from FSS computation
    inds = np.logical_and(reference_fractions >= -small, verified_fractions >= -small).nonzero()
    mse     = np.nansum( np.square(reference_fractions[inds]  - verified_fractions[inds]) )
    mse_ref = np.nansum( np.square(reference_fractions[inds]) + np.square(verified_fractions[inds]) )
    if np.isclose(mse_ref, 0.):
        #no data is present or too small a search radius
        this_fss = 0.
        fss_difference = - 1.
    else:
        this_fss = 1. - mse / mse_ref
        fss_difference = this_fss - target_fss

    #print(mode, ('{:8.4f}'*4).format(radius, this_fss, target_fss, fss_difference))

    #return difference with FSS target
    if debug:
        return fss_difference, reference_fractions, verified_fractions
    else:
        #normal mode
        return fss_difference


def to_xyz(lons, lats):
    import numpy as np
    import scipy.spatial
    import cartopy.crs as ccrs

    from domutils.geo_tools.lat_lon_extend import lat_lon_extend
    """ From lat/lon to xyz on unit sphere
    
    Args:
        lons, lats : coords to be converted to xyz
    """

    #insure numpy arrays
    xx=np.asarray(lons)
    yy=np.asarray(lats)

    #everything to xyz coords 
    proj_ll = ccrs.Geodetic()
    geo_cent = proj_ll.as_geocentric()

    return geo_cent.transform_points(proj_ll,
                                     xx.flatten(),
                                     yy.flatten())


def lmin_from_fss(reference_true, reference_qi, verified_true, mode,
                  lmin_range,
                  latitudes=None, longitudes=None, 
                  grid_dx=None, n_cpus=1, use_qi=True, dask_client_exists=False):

    """minimum scale at which forecast has skill

    lmin from Fraction Skill Score

    it is assumed that reference an verified data are already on the same verification grid

    arguments:
        reference_true: [unitless] 1 when reference field > threshold; 0 otherwise
        reference_qi:   [unitless] quality index of observations
        verified_true:  [unitless] 1 when verified  field > threshold; 0 otherwise
        mode:           [str]   name of method to used for computing FSS, see 'fss_diff' doc for valuid options
        lmin_range:     [min,max] in km range of radius between which lmin will be searched. Set min=max to skip lmin search.
        latitudes:      [degrees] latitude of grid  ; only for "manual" methods
        longitudes:     [degrees] longitude of grid ; only for "manual" methods
        grid_dx:        [km] size of grid; tile necessary for 'fft' method
        n_cpus:         Number of cpus we have for the job only used for 'manual_parallel' method
        dask_client_exists: if True, no attempts will be made at initializing dask client
        
    """
    #import os
    #os.environ["OMP_NUM_THREADS"] = "1"        # export OMP_NUM_THREADS=1
    #os.environ["OPENBLAS_NUM_THREADS"] = "1"   # export OPENBLAS_NUM_THREADS=1
    #os.environ["MKL_NUM_THREADS"] = "1"        # export MKL_NUM_THREADS=1
    #os.environ["VECLIB_MAXIMUM_THREADS"] = "1" # export VECLIB_MAXIMUM_THREADS=1
    #os.environ["NUMEXPR_NUM_THREADS"] = "1"    # export NUMEXPR_NUM_THREADS=1   

    import sys
    import os
    import time
    import warnings
    import numpy as np
    import scipy.spatial
    import scipy.optimize
    import dask.distributed


    #skip lmin search if limits of range are the same
    if np.allclose([lmin_range[0]], [lmin_range[1]]):
        return None

    #make sure that all inputs have same shape
    if (reference_true.shape != reference_qi.shape) or (reference_true.shape != verified_true.shape) :
        raise ValueError('all inputs must have same shape')

    #target fss for a "usefull" forecast
    target_fss = 0.5 + ( np.sum(reference_qi*reference_true) / np.sum(reference_qi) )/2.

    #initialize dask client if needed
    if (mode == 'manual_parallel') and (not dask_client_exists):
        #parallel execution, initialize dask client
        client = dask.distributed.Client(processes=True, threads_per_worker=1, n_workers=n_cpus, silence_logs=40)


    #find lmin 
    try:
        lmin_v, r = scipy.optimize.brentq(fss_diff, lmin_range[0], lmin_range[1], 
                                        args=(target_fss, mode,
                                              reference_true, reference_qi, verified_true, grid_dx),
                                        xtol=1., rtol=1e-6, maxiter=100, full_output=True, disp=False)
        #get out of loop if we converged
        if not r.converged:
            print('lmin did not converge ')
            lmin_v = None
     
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)
    except:
        print('lmin did not converge ')
        lmin_v = None

    ##for debugging
    #lmin_v = 1.
    #lmin_min = 15.
    #lmin_max = 2000
    #for radius in np.arange(lmin_min,lmin_max, 10):
    #    print(f'radius: {radius}, target FSS: {target_fss}')

    #    #method 1
    #    mode = 'manual_serial'
    #    t1 = time.time()
    #    this_fss_diff = fss_diff(radius, target_fss, mode, 
    #                             reference_true, reference_qi, verified_true, grid_dx,
    #                             verif_longitudes=longitudes, verif_latitudes=latitudes)
    #    t2 = time.time()
    #    print(mode, 'time: ', t2-t1, 'fss_diff', this_fss_diff)

    #    #method 2
    #    mode = 'manual_parallel'
    #    t1 = time.time()
    #    this_fss_diff, ref_frac_parallel, verif_frac_parallel = fss_diff(radius, target_fss, mode, 
    #                                                                     reference_true, reference_qi, verified_true, grid_dx,
    #                                                                     verif_longitudes=longitudes, verif_latitudes=latitudes, 
    #                                                                     n_cpus=40, debug=True)
    #    t2 = time.time()
    #    print(mode, 'time: ', t2-t1, 'fss_diff', this_fss_diff)

    #    #method 3
    #    mode = 'fft'
    #    t1 = time.time()
    #    this_fss_diff, ref_frac_convol, verif_frac_convol = fss_diff(radius, target_fss, mode, 
    #                                                                 reference_true, reference_qi, verified_true, grid_dx,
    #                                                                 debug=True)
    #                             
    #    t2 = time.time()
    #    print(mode, 'time: ', t2-t1, 'fss_diff', this_fss_diff)

    #    ###show image for verification
    #    #import compare_fields
    #    #compare_fields.plot_fraction(reference_true, longitudes, latitudes, 
    #    #                             rf=ref_frac_parallel,    rfi=ref_frac_convol,
    #    #                             vf=verif_frac_parallel,vfi=verif_frac_convol,
    #    #                             radius=radius)
    #exit()



    return lmin_v




def main():

    import datetime
    import numpy as np
    import domcmc.fst_tools as fst_tools



    ##Example 1---------------------------------------------------------------
    ##variables controlling the verification
    #threshold = .1  #[mm/h]
    #min_qi = .2
    #lmin_max=10

    ##variables controlling the execution
    #n_cpus = 3

    ##data
    #latitudes = np.array([[51.82844 , 51.850636, 51.872826, 51.895023],
    #                      [51.824722, 51.846912, 51.869102, 51.89129 ],
    #                      [51.820988, 51.84318 , 51.865364, 51.887558],
    #                      [51.817253, 51.839447, 51.861626, 51.88382 ]])
    #longitudes= np.array([[257.0859 , 257.09192, 257.09793, 257.10394],
    #                      [257.1218 , 257.1278 , 257.13385, 257.1399 ],
    #                      [257.15768, 257.16376, 257.1698 , 257.17584],
    #                      [257.19354, 257.19962, 257.2057 , 257.21176]])

    #reference_pr = np.array([[ 0,  0,  0,  0],
    #                         [ 0,  1,  0,  0],
    #                         [ 0,  0,  0,  0],
    #                         [ 0,  0,  0,  0]])

    ##reference_qi = np.array([[ 0,  0,  0,  0],
    ##                         [ 0,  1,  0,  0],
    ##                         [ 0,  0,  0,  0],
    ##                         [ 0,  0,  0,  0]])

    ##reference_qi = np.array([[ 0,  0,  0,  0],
    ##                         [ 0,  1,  1,  0],
    ##                         [ 0,  1,  1,  0],
    ##                         [ 0,  0,  0,  0]])

    #reference_qi = np.array([[ 1,  1,  1,  1],
    #                         [ 1,  1,  1,  1],
    #                         [ 1,  1,  1,  1],
    #                         [ 1,  1,  1,  1]])

    #verified_pr  = np.array([[ 0,  0,  0,  0],
    #                         [ 0,  0,  0,  0],
    #                         [ 0,  0,  1,  0],
    #                         [ 0,  0,  0,  0]])
    #
    #lmin(reference_pr, reference_qi, verified_pr, 
    #     latitudes, longitudes, 
    #     threshold, min_qi, 
    #     lmin_max,
    #     grid_dx,
    #     n_cpus)

    



    #Example 2---------------------------------------------------------------
    #reference data
    this_date = datetime.datetime(2016,7,1,1,00)
    
    radar_dir = '/space/hall4/sitestore/eccc/mrd/rpndat/dja001/lhn_input/r_data_h5_v8_smooth_04_median_03_min_natgrid2.5/'
    radar_recipe = '%Y/%m/%d/%Y%m%d%H%M_mosaic.fst'
    reference_file = radar_dir+this_date.strftime(radar_recipe)
    
    reference_pr_dict = fst_tools.get_data(file_name=reference_file, var_name='RDPR', latlon=True)
    reference_qi_dict = fst_tools.get_data(file_name=reference_file, var_name='RDQI')

    #select data only on verification grid
    domain_dict = {'radars':[200,  50,   2300, 700] }
    imin,jmin,imax,jmax = domain_dict['radars']
    reference_pr = reference_pr_dict['values'][imin:imax,jmin:jmax]
    reference_qi = reference_qi_dict['values'][imin:imax,jmin:jmax]
    latitudes  = reference_pr_dict['lat'][imin:imax,jmin:jmax]
    longitudes = reference_pr_dict['lon'][imin:imax,jmin:jmax]
    grid_dx = 2.5

    
    ##forecast data
    prefix = '2016070100' #start time of forecast
    fcst_output_dir = '/space/hall3/sitestore/eccc/mrd/rpndat/dja001/maestro_archives/N2CC801E16V1/gridpt/prog/lhn/'
    #get precipitation rate from PR diff
    fcst_pr_t_dict   = fst_tools.get_data(dir_name=fcst_output_dir, var_name='PR', prefix=prefix, datev=this_date)
    deltat = 10.*60. #[seconds] -> 10 min 
    date_mdt = this_date - datetime.timedelta(seconds=deltat)
    fcst_pr_mdt_dict = fst_tools.get_data(dir_name=fcst_output_dir, var_name='PR', prefix=prefix, datev=date_mdt)
    
    #forecast precip rate in mm/h
    #       *1000   -> conversion from meters to mm
    #       *3600   -> for precip rate during one hour
    #       /deltat -> time difference between the two accumulation (PR) values that were read
    verified_pr = (fcst_pr_t_dict['values'] - fcst_pr_mdt_dict['values'])*1000.*3600/deltat
    verified_pr = verified_pr[imin:imax,jmin:jmax]
    
    #variables controlling the verification
    threshold = .1  #[mm/h]
    min_qi = .2
    #use None for inclusion of end point
    lmin_range=[grid_dx, 500]

    #quality index < min_qi set to zero
    reference_qi   = np.where(reference_qi < min_qi,  0., reference_qi)

    #apply threshold on quantities
    reference_true = np.where(reference_pr >= threshold, 1., 0.)
    verified_true  = np.where(verified_pr  >= threshold, 1., 0.)

    ##variables controlling the execution
    n_cpus = 40

    #import dask.distributed
    #client = dask.distributed.Client(processes=True, threads_per_worker=1, n_workers=n_cpus, silence_logs=40)


    lminv = lmin(reference_true, reference_qi, verified_true, 'fft',
                 lmin_range, grid_dx=grid_dx)
                 #latitudes=latitudes, longitudes=longitudes,
                 #n_cpus=n_cpus, dask_client_exists=True)

    print('converged to lmin = ', lminv)

if __name__ =='__main__':
    main()
