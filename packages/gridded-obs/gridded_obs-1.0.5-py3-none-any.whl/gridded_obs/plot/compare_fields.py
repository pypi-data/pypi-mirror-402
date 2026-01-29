def plot_circles(ax, lats, lons, radius):

    #plot circles to debug lmin code
    import cartopy
    import cartopy.crs 
    import domutils.geo_tools as geo_tools
    import numpy as np

    #plot radar circles  
    proj_cart = cartopy.crs.PlateCarree()
    transform = proj_cart._as_mpl_transform(ax)
    azimuths = np.arange(0.,361)
    for this_lat, this_lon in zip(lats.ravel(),lons.ravel()):
        ranges   = np.full_like(azimuths, radius)
        lon1_arr = np.full_like(azimuths, this_lon)
        lat1_arr = np.full_like(azimuths, this_lat)
        rlons, rlats = geo_tools.lat_lon_range_az(lon1_in   =   lon1_arr, 
                                                  lat1_in   =   lat1_arr,
                                                  range_in  =   ranges,
                                                  azimuth_in=   azimuths)
        #circles
        color=(0./256.,81./256.,237./256.)
        ax.plot(rlons, rlats, transform=proj_cart, c=color, zorder=300, linewidth=.1)
        ax.scatter(this_lon, this_lat, transform=proj_cart, color=color, zorder=300, s=1.**2.)

        break



def plot_geo(ax):
    import cartopy.feature as cfeature

    #ax.outline_patch.set_linewidth(.3)
    ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.2, edgecolor='0.6')




def compare_fields(reference_v, reference_qi, verified_v,
                   latitudes, longitudes, 
                   this_domain, params, t0_date, leadtime, 
                   threshold=None, radius=None):
    """image of reference,quality index and verified fields
    """

    import datetime
    import os
    import numpy as np
    import pickle
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import domcmc.fst_tools as fst_tools
    import domutils.legs as legs
    import domutils.geo_tools as geo_tools
    import domutils.radar_tools as radar_tools
    import domutils._py_tools as py_tools
    import gridded_obs.plot 


    #date that will be displayed
    this_date = t0_date + leadtime

    #missing val
    missing = -9999.

    #units
    if params.quantity == 'precip_rate':
        units = '[mm/h]'
    elif params.quantity == 'accumulation':
        units = '[mm]'
    elif params.quantity == 'accum_one_pr':
        units = '[mm]'
    else:
        raise ValueError('Code should not get here ;)')

    #figure dimensions
    #ratio  = 0.5
    #ratio  = 0.888
    rec_w  = 6.           # Horizontal size of a panel
    rec_h  = params.ratio[params.verif_domains[0]]*rec_w  # Vertical size of a panel
    rec_hist  = 0.5*rec_w  # Vertical size of a panel
    sp_w   = .2           # horizontal space between panels
    sp_h   = 1.           # vertical space between panels
    pal_sp = .05           # spavce between panel and palette
    pal_w  = .17          # width of palette
    tit_h  = .1           # height of title
    #size of figure
    n_exp  = 4
    n_panels = 2
    fig_w  = 21.
    fig_h  = 12.
    #normalize sizes relative to figure
    rec_w  = rec_w / fig_w
    rec_h  = rec_h / fig_h
    rec_hist  = rec_hist / fig_h
    sp_w   = sp_w / fig_w
    sp_h   = sp_h / fig_h
    pal_sp = pal_sp / fig_w
    pal_w  = pal_w / fig_w
    tit_h  = tit_h / fig_h
    #objects to handle color mappings
    pr_color_map = legs.PalObj(range_arr=[.1,.5,1.,5.,10.,20.,50.],
                                  n_col=6, 
                                  over_high='extend', under_low='white',
                                  excep_val=missing, excep_col='grey_220')
    #larger typeface
    mpl.rcParams.update({'font.size': 18})
    # Use this for editable text in svg
    mpl.rcParams['text.usetex']  = False
    mpl.rcParams['svg.fonttype'] = 'none'
    # Hi def figure
    mpl.rcParams['figure.dpi'] = 600
    #font
    mpl.rcParams['font.family'] = 'Latin Modern Roman'

    #custom pastel color segments for QI index
    pastel = [ [[255,190,187],[230,104, 96]],  #pale/dark red
               [[255,185,255],[147, 78,172]],  #pale/dark purple
               [[255,227,215],[205,144, 73]],  #pale/dark brown
               [[210,235,255],[ 58,134,237]],  #pale/dark blue
               [[223,255,232],[ 61,189, 63]] ] #pale/dark green
    qi_color_map = legs.PalObj(range_arr=[0., 1.],
                               dark_pos='high',
                               color_arr=pastel,
                               excep_val=[missing, 0.],
                               excep_col=['grey_220', 'white'])

    #instantiate figure
    fig = plt.figure(figsize=(fig_w, fig_h))

    #domain dependent quantities
    this_crs = params.crs[this_domain] 
    this_ratio = params.ratio[this_domain]
    this_extent = params.extent[this_domain]
    this_proj_obj = params.proj_inds[this_domain]

    if reference_qi is None:
        #no quality index, we assume everything is good
        reference_qi = np.full_like(reference_v, 1.)    

    #mark model data with no quality index as nodata
    verified_v  = np.where(reference_qi <= 0., missing, verified_v)
    reference_v = np.where(reference_qi <= 0., missing, reference_v)

    #Y position of row
    y0 = sp_h + 1.*(sp_h+rec_hist)
    #title offset
    xp = .04
    yp = 1.03

    #reference values
    x0 = 0.1/fig_w
    pos = [x0, y0, rec_w, rec_h]
    if this_extent is None:
        ax = fig.add_axes(pos, projection=this_crs)
    else:
        ax = fig.add_axes(pos, projection=this_crs)
        ax.set_extent(this_extent, crs=this_crs)
    #title
    ax.annotate('reference_val', size=22, xy=(xp, yp), xycoords='axes fraction')
    #print date only once
    ax.annotate(this_date.strftime('%Y-%m-%d %Hh%M')+f' {params.quantity}', size=24, xy=(xp, 1.2), xycoords='axes fraction')
    #geographical projection of data into axes space
    #ddp
    projected_data = this_proj_obj.project_data(reference_v)
    #draw color figure onto axes
    pr_color_map.plot_data(ax=ax, data=projected_data)
    #format axes and draw geographical boundaries
    this_proj_obj.plot_border(ax, linewidth=.3)
    plot_geo(ax)

    #ii = 245
    #for jj in np.arange(160,180):
    #    lat = latitudes[ii,jj]
    #    lon = longitudes[ii,jj]
    #    proj_cart = ccrs.PlateCarree()
    #    ax.scatter([lon],[lat],s=.1,transform=proj_cart)
    #    print(lat, lon)
    #    print(reference_v[ii,jj], reference_qi[ii,jj])

    #verified_val
    x0 = 0.1/fig_w + sp_w + rec_w
    pos = [x0, y0, rec_w, rec_h]
    if this_extent is None:
        ax2 = fig.add_axes(pos, projection=this_crs)
    else:
        ax2 = fig.add_axes(pos, projection=this_crs)
        ax2.set_extent(this_extent, crs=this_crs)
    #title
    ax2.annotate('verified_val', size=22, xy=(xp, yp), xycoords='axes fraction')
    #geographical projection of data into axes space
    #ddp

    projected_data = this_proj_obj.project_data(verified_v)
    #draw color figure onto axes
    pr_color_map.plot_data(ax=ax2, data=projected_data)
    #format axes and draw geographical boundaries
    this_proj_obj.plot_border(ax2, linewidth=.3)
    plot_geo(ax2)
    #palette
    pal_pos = [x0+rec_w+pal_sp, y0, pal_w, rec_h]
    pr_color_map.plot_palette(pal_pos=pal_pos, 
                                 pal_linewidth=0.3, pal_units=units,
                                 pal_format='{:4.1f}', equal_legs=True)

    #
    #
    #plot circles
    if radius is not None:
        delta_pt = 40
        subset_lat =  latitudes[::delta_pt,::delta_pt]
        subset_lon = longitudes[::delta_pt,::delta_pt]
        plot_circles(ax2, subset_lat, subset_lon, radius)

    ##plot circle selection
    #p_file = '/space/hall3/sitestore/eccc/mrd/rpndat/dja001/lmin_investigate/pts.pickle'
    #with open(p_file, 'rb') as f_handle:
    #    rec_dict = pickle.load(f_handle)
    #p_file = '/space/hall3/sitestore/eccc/mrd/rpndat/dja001/lmin_investigate/ll.pickle'
    #with open(p_file, 'rb') as f_handle:
    #    ll_dict = pickle.load(f_handle)
    #proj_cart = ccrs.PlateCarree()
    #print('number of balls', len(rec_dict['pt_list']))
    #for ball_list in rec_dict['pt_list']:
    #    ax2.scatter(ll_dict['longitudes'][ball_list], ll_dict['latitudes'][ball_list], 
    #                transform=proj_cart, color=(203./256.,26./256.,35./256.),zorder=300, s=.05**2.)




    #reference quality index
    if reference_qi is not None:
        x0 = 0.1/fig_w + 2.*(sp_w + rec_w)+ 5.*sp_w
        pos = [x0, y0, rec_w, rec_h]
        if this_extent is None:
            ax3 = fig.add_axes(pos, projection=this_crs)
        else:
            ax3 = fig.add_axes(pos, projection=this_crs)
            ax3.set_extent(this_extent, crs=this_crs)
        #title
        ax3.annotate('Quality index', size=22, xy=(xp, yp), xycoords='axes fraction')
        #geographical projection of data into axes space
        #ddp
        projected_data = this_proj_obj.project_data(reference_qi)
        #draw color figure onto axes
        qi_color_map.plot_data(ax=ax3, data=projected_data)
        #format axes and draw geographical boundaries
        this_proj_obj.plot_border(ax3, linewidth=.3)
        plot_geo(ax3)
        #palette
        pal_pos = [x0+rec_w+pal_sp, y0, pal_w, rec_h]
        qi_color_map.plot_palette(pal_pos=pal_pos, 
                                  pal_linewidth=0.3, pal_units='[unitless]',
                                  pal_format='{:2.1f}')

    #parameters for hists and dct
    params.exp_list = ['verified']
    params.exp_color = [(255./255., 118./255., 37./255.)]
    params.exp_linestyle = [('-')]
    params.exp_linewidth = [(1.)]

    #Y position of row
    y0 = sp_h + (0.)*(sp_h+rec_h)

    #Histograms 
    x0 = 0.1/fig_w + 0.*(sp_w + rec_w)+ 5.*sp_w
    pos = [x0, y0, rec_w, rec_hist]
    ax4 = fig.add_axes(pos)
    reference_hist, _ = np.histogram(reference_v, bins=params.hist_bin_edges, weights=reference_qi)
    verified_hist, _  = np.histogram(verified_v,  bins=params.hist_bin_edges, weights=reference_qi)
    #add dimensions to make the plotting routine happy
    reference_hist = reference_hist[np.newaxis,:]
    verified_hist  =  verified_hist[np.newaxis,np.newaxis,:]
    gridded_obs.plot.histogram(ax4, params, 0, 
                               params.hist_bin_edges, reference_hist, verified_hist)
    
    #DCT
    x0 = 0.1/fig_w + 1.*(sp_w + rec_w)+ 10.*sp_w
    pos = [x0, y0, rec_w, rec_hist]
    ax5 = fig.add_axes(pos)
    bad_pts = ((reference_qi < params.min_qi) | np.isclose(reference_v, missing) | np.isclose(verified_v, missing)).nonzero()

    reference_pr_for_dct = np.copy(reference_v)
    if bad_pts[0].size > 0:
        reference_pr_for_dct[bad_pts] = 0.
    (reference_wavenum, 
     reference_wavelengths, 
     reference_power) = gridded_obs.pow_dct(reference_pr_for_dct, dx_km=params.grid_dx, n_bands=params.k_nbins)

    verified_pr_for_dct = np.copy(verified_v)
    if bad_pts[0].size > 0:
        verified_pr_for_dct[bad_pts] = 0.
    (verified_wavenum, 
     verified_wavelengths, 
     verified_power) = gridded_obs.pow_dct(verified_pr_for_dct, dx_km=params.grid_dx, n_bands=params.k_nbins)

    #add dimensions to make the plotting routine happy
    reference_power = reference_power[np.newaxis,:]
    verified_power  =  verified_power[np.newaxis,np.newaxis,:]
    gridded_obs.plot.axdct(ax5, params, 0, 
                           reference_wavelengths, reference_power, verified_power)

    #make dir if it does not exist
    if not os.path.isdir(params.figure_dir):
        py_tools.parallel_mkdir(params.figure_dir)

    #figure name
    lt_minutes = leadtime.days*1440. + np.floor(leadtime.seconds/60.)
    if threshold is not None:
        svg_name = params.figure_dir+'/compare_fields_'+t0_date.strftime('%Y%m%d%H%M')+'{:+06.0f}m'.format(lt_minutes)+'_'+this_domain+f'_{threshold:04.1f}mm'+'.svg'
    else:
        svg_name = params.figure_dir+'/compare_fields_'+t0_date.strftime('%Y%m%d%H%M')+'{:+06.0f}m'.format(lt_minutes)+'_'+this_domain+'.svg'
    plt.savefig(svg_name, dpi=400)
    plt.close(fig)
    #py_tools.lmroman(svg_name)
    #py_tools.convert(svg_name,'gif', del_orig=True, density=400, geometry='50%')
    print('done with: ', svg_name)


def plot_fraction(reference_v_in, longitudes, latitudes, 
                  rf=None, rfi=None,
                  vf=None, vfi=None,
                  radius=None):
    """image of fractions for FSS
    """

    if rf is not None:
        reference_fractions = rf
    if rfi is not None:
        reference_fractions_int = rfi
    if vf is not None:
        verified_fractions = vf
    if vfi is not None:
        verified_fractions_int = vfi


    import datetime
    import os
    import numpy as np
    import pickle
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import domcmc.fst_tools as fst_tools
    import domutils.legs as legs
    import domutils.geo_tools as geo_tools
    import domutils.radar_tools as radar_tools
    import domutils._py_tools as py_tools


    #show data only above threshold
    reference_v  = reference_v_in

    #missing val
    missing = -9999.

    #figure dimensions
    ratio  = 0.5
    rec_w  = 6.           # Horizontal size of a panel
    rec_h  = ratio*rec_w  # Vertical size of a panel
    sp_w   = .2           # horizontal space between panels
    sp_h   = 1.           # vertical space between panels
    pal_sp = .05           # spavce between panel and palette
    pal_w  = .17          # width of palette
    tit_h  = .1           # height of title
    #size of figure
    n_exp  = 4
    n_panels = 2
    fig_w  = 21.
    fig_h  = 9.
    #normalize sizes relative to figure
    rec_w  = rec_w / fig_w
    rec_h  = rec_h / fig_h
    sp_w   = sp_w / fig_w
    sp_h   = sp_h / fig_h
    pal_sp = pal_sp / fig_w
    pal_w  = pal_w / fig_w
    tit_h  = tit_h / fig_h
    #pixel resolution of image being generated
    grid_w_pts = 1200.
    image_dpi = grid_w_pts/(rec_w*fig_w)
    image_res = [grid_w_pts,ratio*grid_w_pts]
    #objects to handle color mappings
    pr_color_map = legs.PalObj(range_arr=[.1,.5,1.,5.,10.,20.,50.],
                                  n_col=6, 
                                  over_high='extend', under_low='white',
                                  excep_val=missing, excep_col='grey_220')
    #larger typeface
    mpl.rcParams.update({'font.size': 18})
    # Use this for editable text in svg
    mpl.rcParams['text.usetex']  = False
    mpl.rcParams['svg.fonttype'] = 'none'
    # Hi def figure
    mpl.rcParams['figure.dpi'] = 600

    #custom pastel color segments for QI index
    pastel = [ [[255,190,187],[230,104, 96]],  #pale/dark red
               [[255,185,255],[147, 78,172]],  #pale/dark purple
               [[255,227,215],[205,144, 73]],  #pale/dark brown
               [[210,235,255],[ 58,134,237]],  #pale/dark blue
               [[223,255,232],[ 61,189, 63]] ] #pale/dark green
    qi_color_map = legs.PalObj(range_arr=[0., .2],
                               dark_pos='high',
                               color_arr=pastel,
                               over_under='extend',
                               excep_val=[missing, 0.,-1.],
                               excep_col=['grey_220', 'white', 'dark_red'])


    #instantiate figure
    fig = plt.figure(figsize=(fig_w, fig_h))

    proj_obj_list = [proj_obj_full]
    crs_list      = [crs_full]
    extent_list   = [map_extent_full]

    for ii, [this_proj_obj, this_crs, this_extent] in enumerate(zip(proj_obj_list,crs_list,extent_list)):

        #title offset
        xp = .04
        yp = 1.01

        #reference values
        x0 = 0.1/fig_w
        y0 = sp_h + (1.-ii)*(sp_h+rec_h)
        pos = [x0, y0, rec_w, rec_h]
        ax = fig.add_axes(pos, projection=crs, extent=this_extent)
        #title
        ax.annotate('reference_val', size=22, xy=(xp, yp), xycoords='axes fraction')
        #print date only once
        #if ii ==0:
            #ax.annotate(this_date.strftime('%Y-%m-%d %Hh%M'), size=24, xy=(xp, 1.2), xycoords='axes fraction')
        #geographical projection of data into axes space
        #ddp
        projected_data = this_proj_obj.project_data(reference_v)
        #draw color figure onto axes
        pr_color_map.plot_data(ax=ax, data=projected_data)
        #format axes and draw geographical boundaries
        plot_geo(ax)
        #palette
        pal_pos = [x0+rec_w+pal_sp, y0, pal_w, rec_h]
        pr_color_map.plot_palette(pal_pos=pal_pos, 
                                  pal_linewidth=0.3, pal_units='[mm/h]',
                                  pal_format='{:3.0f}', equal_legs=True)


        #full grid computation
        if rf is not None:
            x0 = 0.1/fig_w + 1.*(sp_w + rec_w)+ 5.*sp_w
            y0 = sp_h + (1.-ii)*(sp_h+rec_h)
            pos = [x0, y0, rec_w, rec_h]
            ax2 = fig.add_axes(pos, projection=this_crs)
            ax2.set_extent(this_extent, crs=this_crs)
            #title
            ax2.annotate('reference fractions', size=22, xy=(xp, yp), xycoords='axes fraction')
            #geographical projection of data into axes space
            #ddp
            projected_data = this_proj_obj.project_data(reference_fractions)
            #draw color figure onto axes
            qi_color_map.plot_data(ax=ax2, data=projected_data)
            #format axes and draw geographical boundaries
            plot_geo(ax2)
            ##palette
            #pal_pos = [x0+rec_w+pal_sp, y0, pal_w, rec_h]
            #qi_color_map.plot_palette(pal_pos=pal_pos, 
            #                             pal_linewidth=0.3, pal_units='[mm]',
            #                             pal_format='{:3.0f}', equal_legs=True)

        #
        if vf is not None:
            x0 = 0.1/fig_w + 1.*(sp_w + rec_w)+ 5.*sp_w
            y0 = sp_h + (0.-ii)*(sp_h+rec_h)
            #
            x0 = 0.1/fig_w + 1.*(sp_w + rec_w)+ 5.*sp_w
            pos = [x0, y0, rec_w, rec_h]
            ax3 = fig.add_axes(pos, projection=this_crs, extent=this_extent)
            #title
            ax3.annotate('verified fractions', size=22, xy=(xp, yp), xycoords='axes fraction')
            #geographical projection of data into axes space
            #ddp
            projected_data = this_proj_obj.project_data(verified_fractions)
            #draw color figure onto axes
            qi_color_map.plot_data(ax=ax3, data=projected_data)
            #format axes and draw geographical boundaries
            plot_geo(ax3)
            ##palette
            #pal_pos = [x0+rec_w+pal_sp, y0, pal_w, rec_h]
            #qi_color_map.plot_palette(pal_pos=pal_pos, 
            #                             pal_linewidth=0.3, pal_units='[mm]',
            #                             pal_format='{:3.0f}', equal_legs=True)


        ##
        ##
        ##plot circles
        #if radius is not None:
        #    delta_pt = 40
        #    subset_lat =  latitudes[::delta_pt,::delta_pt]
        #    subset_lon = longitudes[::delta_pt,::delta_pt]
        #    plot_circles(ax2, subset_lat, subset_lon, radius)

        ##plot circle selection
        #p_file = '/space/hall3/sitestore/eccc/mrd/rpndat/dja001/lmin_investigate/pts.pickle'
        #with open(p_file, 'rb') as f_handle:
        #    rec_dict = pickle.load(f_handle)
        #p_file = '/space/hall3/sitestore/eccc/mrd/rpndat/dja001/lmin_investigate/ll.pickle'
        #with open(p_file, 'rb') as f_handle:
        #    ll_dict = pickle.load(f_handle)

        #proj_cart = ccrs.PlateCarree()
        #print('number of balls', len(rec_dict['pt_list']))
        #for ball_list in rec_dict['pt_list']:
        #    ax2.scatter(ll_dict['longitudes'][ball_list], ll_dict['latitudes'][ball_list], 
        #                transform=proj_cart, color=(203./256.,26./256.,35./256.),zorder=300, s=.05**2.)



        #reference_fractions_int  = np.where(reference_fractions_int < 0., -1., reference_fractions_int)
        #verified_fractions_int   = np.where(verified_fractions_int < 0., -1., verified_fractions_int)

        if rfi is not None:
            x0 = 0.1/fig_w + 2.*(sp_w + rec_w)+ 5.*sp_w
            y0 = sp_h + (1.-ii)*(sp_h+rec_h)
            pos = [x0, y0, rec_w, rec_h]
            ax4 = fig.add_axes(pos, projection=this_crs, extent=this_extent)
            #title
            ax4.annotate('reference interpolated', size=22, xy=(xp, yp), xycoords='axes fraction')
            #geographical projection of data into axes space
            #ddp
            projected_data = this_proj_obj.project_data(reference_fractions_int)
            #draw color figure onto axes
            qi_color_map.plot_data(ax=ax4, data=projected_data)
            #format axes and draw geographical boundaries
            plot_geo(ax4)
            #palette
            pal_pos = [x0+rec_w+pal_sp, y0, pal_w, rec_h]
            qi_color_map.plot_palette(pal_pos=pal_pos, 
                                      pal_linewidth=0.3, pal_units='[unitless]',
                                      pal_format='{:2.1f}')
        #
        if vfi is not None:
            x0 = 0.1/fig_w + 2.*(sp_w + rec_w)+ 5.*sp_w
            y0 = sp_h + (0.-ii)*(sp_h+rec_h)
            #reference fraction
            x0 = 0.1/fig_w + 2.*(sp_w + rec_w)+ 5.*sp_w
            pos = [x0, y0, rec_w, rec_h]
            ax5 = fig.add_axes(pos, projection=this_crs, extent=this_extent)
            #title
            ax5.annotate('verified interpolated', size=22, xy=(xp, yp), xycoords='axes fraction')
            #geographical projection of data into axes space
            #ddp
            projected_data = this_proj_obj.project_data(verified_fractions_int)
            #draw color figure onto axes
            qi_color_map.plot_data(ax=ax5, data=projected_data)
            #format axes and draw geographical boundaries
            plot_geo(ax5)
            #palette
            pal_pos = [x0+rec_w+pal_sp, y0, pal_w, rec_h]
            qi_color_map.plot_palette(pal_pos=pal_pos, 
                                      pal_linewidth=0.3, pal_units='[unitless]',
                                      pal_format='{:2.1f}')

    #make dir if it does not exist
    pic_dir='/space/hall3/sitestore/eccc/mrd/rpndat/dja001/test_new_griddedobs/' 
    if not os.path.isdir(pic_dir):
        domutils._py_tools.parallel_mkdir(pic_dir)

    #figure name
    #if not np.isclose(leadtime.seconds, 0):
    #    lt_minutes = leadtime.days*1440. + np.floor(leadtime.seconds/60.)
    #    svg_name = pic_dir+'/compare_fields_'+validity_date.strftime('%Y%m%d%H%M')+'{:+06.0f}m_th{:04.1f}'.format(lt_minutes, threshold)+'.svg'
    #else:
    #    svg_name = pic_dir+'/compare_fields_'+validity_date.strftime('%Y%m%d%H%M')+'_th{:03.0f}'.format(threshold)+'.svg'
    svg_name = pic_dir+'/compare_fractions_radius'+'{:05.2f}'.format(radius)+'.svg'
    plt.savefig(svg_name, dpi=image_dpi)
    plt.close(fig)
    #py_tools.lmroman(svg_name)
    #py_tools.convert(svg_name,'gif', del_orig=True, density=400, geometry='50%')
    print('done with: ', svg_name)


if __name__ == "__main__":     
    main()
