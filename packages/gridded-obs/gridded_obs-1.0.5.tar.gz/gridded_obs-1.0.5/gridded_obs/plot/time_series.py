



def time_series(params, threshold, domain, score_dict):
    """plot time series

    what is being plotted is defined in params.time_series from the bottom up
    """

    import numpy as np
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import domcmc.fst_tools as fst_tools
    import domutils.legs as legs
    import domutils.geo_tools as geo_tools
    import domutils.radar_tools as radar_tools
    import gridded_obs.plot

    n_panels  = len(params.time_series)

    #missing val
    missing = -9999.
    small=1e-3

    #leadtime being verified
    leadtime_hours = np.array([ lt.days*24. + lt.seconds/3600. for lt in params.leadtime_list])
    xticks = np.arange(leadtime_hours[0], leadtime_hours[-1]+small,3.)

    #figure dimensions
    ratio  = 0.15
    rec_w  = 10.           # Horizontal size of a panel
    rec_h  = ratio*rec_w  # Vertical size of a panel
    sp_w   = 1.2           # horizontal space between panels
    sp_h   = .2           # vertical space between panels
    pal_sp = .05          # space between panel and palette
    pal_w  = .17          # width of palette
    tit_h  = 1.6 + 0.5*np.ceil(len(params.exp_list)/2.)  # height of title
    #size of figure
    fig_w  = rec_w + 2. * sp_w
    fig_h  = sp_h + (n_panels)*(rec_h+sp_h) + tit_h + .9
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
    image_res = [grid_w_pts,ratio*grid_w_pts]

    #larger typeface
    mpl.rcParams.update({'font.size': 20})
    # Use this for editable text in svg
    mpl.rcParams['text.usetex']  = False
    mpl.rcParams['svg.fonttype'] = 'none'
    # Hi def figure
    mpl.rcParams['figure.dpi'] = 600

    #dictionary for vertical range of pannels
    r_dict = {}
    if params.ylim_pod is not None:
        r_dict['pod'] = params.ylim_pod
    else:
        r_dict['pod'] = gridded_obs.plot.autorange(score_dict['pod'])
    if params.ylim_far is not None:
        r_dict['far'] = params.ylim_far
    else:
        r_dict['far'] =  gridded_obs.plot.autorange(score_dict['far'])
    if params.ylim_csi is not None:
        r_dict['csi'] = params.ylim_csi
    else:
        r_dict['csi'] =  gridded_obs.plot.autorange(score_dict['csi'])
    if params.ylim_fbias is not None:
        r_dict['fbias'] = params.ylim_fbias
    else:
        r_dict['fbias'] =  gridded_obs.plot.autorange(score_dict['fbias'])
    if params.ylim_lmin is not None:
        r_dict['lmin'] = params.ylim_lmin
    else:
        r_dict['lmin'] =  gridded_obs.plot.autorange(score_dict['lmin'])
    if params.ylim_corr_coeff is not None:
        r_dict['corr_coeff'] = params.ylim_corr_coeff
    else:
        r_dict['corr_coeff'] =  gridded_obs.plot.autorange(score_dict['corr_coeff'])

    unit_dict = {'fbias':'unitless', 
                 'pod':'unitless', 
                 'far':'unitless', 
                 'csi':'unitless', 
                 'lmin':'radius [km]',
                 'corr_coeff':'unitless'}

    #instantiate figure
    fig = plt.figure(figsize=(fig_w, fig_h))

    #header, legend and other explanations
    gridded_obs.plot.plot_header(fig, domain, params,
                                 fig_w  , fig_h  ,
                                 rec_w  , rec_h,
                                 sp_w   , sp_h,
                                 pal_sp , pal_w,
                                 tit_h, threshold=threshold,
                                 show_reference=False)


    x0 = sp_w
    for nn, score in enumerate(params.time_series):
        #plot panels one by one
        y0 = sp_h + nn*(rec_h + sp_h) + 1./fig_h

        pos = [x0, y0, rec_w, rec_h]

        y_lim = r_dict[score]

        #Setup the general look 
        #Ticks length and width
        major_height = 5
        major_width = .3
        minor_height = 2
        minor_width = .3
        #axes containing data
        ax = fig.add_axes(pos, label = 'time_series', zorder=10)
        ax.set_facecolor((0.,0.,0.,0.))
        ax.set_xlim((leadtime_hours[0], leadtime_hours[-1]))
        ax.set_ylim(y_lim)
        ax.tick_params(axis='both', which='both', direction='in', top='on', right=True)
        ax.set_xticks(xticks)
        #ax.set_yticks(this_var_info['ticks']) 
        ax.tick_params('both', length=major_height, width=major_width, which='major')
        ax.tick_params('both', length=minor_height, width=minor_width, which='minor')
        if nn == 0:
            ax.set_xlabel('Leadtime (h)')
        else:
            ax.set_xticklabels([])
        ax.set_ylabel(unit_dict[score])
        #ax.yaxis.set_minor_locator(plt.MultipleLocator(this_var_info['minor_tick_separation']))

        #horizontal line for frequency bias
        if score == 'fbias':
            ax.axhline(1., color='black', zorder=1, linewidth=0.5)

        #thinner lines for axis, god is this syntax ugly...
        for axis in ['top','bottom','left','right']:
              ax.spines[axis].set_linewidth(0.3)

        #greyed out zone in panels
        if params.leadtime_greyed_out is not None:
            if not np.isclose(params.leadtime_greyed_out[0], params.leadtime_greyed_out[1]):
                gc = 220./255.
                g_xmin = params.leadtime_greyed_out[0]/60.
                g_xmax = params.leadtime_greyed_out[1]/60.
                g_width = g_xmax - g_xmin
                g_height = y_lim[1] - y_lim[0]
                #        y,         width,     height,     left
                ax.barh([y_lim[0]], [g_width], [g_height], left=g_xmin, align='edge', color=(gc,gc,gc,1.), edgecolor=(1.,1.,1.,0.), zorder=0)
    
        #plot name of score on panel
        ax.annotate(score.upper(), (0.02, 0.8), clip_on=False, xycoords='axes fraction',\
                    ha='left', va='center', fontsize=28)
        print('minmax: ',score, np.nanmin(score_dict[score]), np.nanmax(score_dict[score]))


        for kk, experiment in enumerate(params.exp_list):

            if params.show_obs_num:
                #plot number of data points in each bin
                #y position of numbers 
                yp = y_lim[0] + (1. - 0.09*kk - 0.09) * (y_lim[1] - y_lim[0])
                #30 number are legible
                mod_num = 1.
                while len(leadtime_hours)/mod_num > 30.:
                    mod_num *= 2.
                #print numbers
                for nn, (leadtime, count) in enumerate(zip(leadtime_hours, score_dict['n_'+score][:,kk])):
                    if np.mod(nn,mod_num):
                        #skip some entries to make the whole thing legible
                        continue
                    elif (nn == 0):
                        continue
                    else:
                        ax.text(leadtime, yp, '{:d}'.format(int(count)), fontsize=9, color=params.exp_color[kk], 
                                ha='center', va = 'center', alpha = 0.3)

            #plot time series for each experiments
            ax.plot(   leadtime_hours, score_dict[score][:,kk], color=params.exp_color[kk], 
                                                                linestyle=params.exp_linestyle[kk], 
                                                                linewidth=params.exp_linewidth[kk], 
                                                                clip_on=False, )

    
    #save figure
    svg_name = params.figure_dir+'/time_series__'+domain+'__{:09.4f}'.format(threshold)+'.svg'
    gridded_obs.plot.save_n_close(fig, svg_name, params)

        



