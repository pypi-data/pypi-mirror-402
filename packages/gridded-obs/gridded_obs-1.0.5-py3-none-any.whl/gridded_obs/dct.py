
#test code for making suer DCT code does what we think its doing

def pow_dct(src_data, dx_km=None, n_bands=None):
    """ compute power spectrum from DCT 

    Following Denis et al 2008  https://doi.org/10.1175/1520-0493(2002)130<1812:SDOTDA>2.0.CO;2


    src_data:   2D array-like,  the field whose spectrum is desired
    dx_km:      float,          grid spacing, delta x, in km
    n_bands:    integer,        number of desired averaging bands. Should not be smaller than smallest domain dimension
    """
    import numpy as np
    from scipy.fft import dctn #idctn

    #ensure input is numpy array
    src_np = np.asarray(src_data)

    if dx_km is None:
        raise ValueError('Grid delta x;  dx_km must be specified')

    if n_bands is None:
        raise ValueError('The number of averaging bands n_bands must be specified')

    #maximum wavenumber (k) is the smallest dimension of the domain
    ni, nj = src_np.shape
    max_k = np.min([ni,nj])

    if n_bands > max_k:
        raise ValueError('The number of averaging bands n_bands must not be larger than the smallest dimension of the domain')
    
    m, n = np.meshgrid(np.arange(ni), np.arange(nj), indexing='ij')
    #2D wavenumber
    k2d = np.sqrt(m**2. + n**2.)
    #2D normalized wavenumber
    alpha = np.sqrt(m**2./ni**2 + n**2./nj**2.)
    with np.errstate(divide='ignore' ): 
        #we allow division by zero for alpha(0,0) which we don't use
        wavelength_km = 2.*dx_km / alpha
    
    #bounds for the averaging bands 
    k_bounds = np.geomspace(1., max_k, n_bands+1)
    
    #compute DCT
    dct = dctn(src_np, norm='ortho')
    #Eq. 5 from Denis et al F square / N_total
    sigma_square = dct**2. / (ni*nj)

    #average wavenumber, wavelength and DCT power within bands
    mean_k          = np.full(n_bands, np.nan)
    mean_wavelength = np.full(n_bands, np.nan)
    mean_power      = np.full(n_bands, np.nan)
    for ii, (k_low, k_high) in enumerate(zip(k_bounds[:-1],k_bounds[1:])):
        alpha_low  = k_low / max_k
        alpha_high = k_high / max_k
        inds = np.logical_and(alpha > alpha_low, alpha <= alpha_high).nonzero()
        if inds[0].size == 0:
            #no data in band, this happens
            continue
        else:
            mean_k[ii]          = np.mean(k2d[inds])
            mean_wavelength[ii] = np.mean(wavelength_km[inds])
            mean_power[ii]      = np.mean(sigma_square[inds])

    return mean_k, mean_wavelength, mean_power     




def main():



    import numpy as np
    import scipy.signal
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    import domutils._py_tools as d_py
    import gc

    #  #1
    #
    #simple and small example 
    
    src = [[1,   0.5,  0.3, 0.2], 
           [0.5, 0.3,  0.3, 0.1], 
           [0.3, 0.2,  0.3, 0.05], 
           [0.2, 0.1,  0.1, 0.02], 
           [0.1, 0.05, 0.02, 0.01]]
    
    dx_km = 2.5
    n_bands = 4
    mean_wavenum, mean_wavelength, mean_power = pow_dct(src, dx_km=dx_km, n_bands=n_bands)
    
    print('mean_wavenum')
    print(mean_wavenum)
    print('mean_wavelength')
    print(mean_wavelength)
    print('mean_power')
    print(mean_power)


    #  #2
    #
    #Gaussian bell mock data
    npts = 1024
    half_npts = int(npts/2)
    x = np.linspace(-1., 1, half_npts+1)
    y = np.linspace(-1., 1, half_npts+1)
    xx, yy = np.meshgrid(x, y)
    gauss_bulge = np.exp(-(xx**2 + yy**2) / .6**2)

    #radar looking mock data
    sigma1 = .03
    sigma2 = .25
    np.random.seed(int(3.14159*100000))
    rand = np.random.normal(size=[npts,npts])
    xx, yy = np.meshgrid(np.linspace(-1.,1.,num=half_npts),np.linspace(1.,-1.,num=half_npts))
    kernel1 = np.exp(-1.*np.sqrt(xx**2.+yy**2.)/.02)
    kernel2 = np.exp(-1.*np.sqrt(xx**2.+yy**2.)/.15)
    reflectivity_like = (   scipy.signal.fftconvolve(rand,kernel1,mode='valid')
                          + scipy.signal.fftconvolve(rand,kernel2,mode='valid') )
    reflectivity_like = ( reflectivity_like / np.max(np.absolute(reflectivity_like.max())) * 62. )
    reflectivity_like = reflectivity_like[0:256,:]


    dx_km = 2.5
    n_bands = 50
    mean_wavenum, mean_wavelength, mean_power = pow_dct(reflectivity_like, dx_km=dx_km, n_bands=n_bands)

    #plot showing both wavenumber and wavelength

    #larger typeface
    mpl.rcParams.update({'font.size': 24})
    # Use this for editable text in svg
    mpl.rcParams['text.usetex']  = False
    mpl.rcParams['mathtext.fontset'] = 'cm'
    mpl.rcParams['svg.fonttype'] = 'none'
    #prevent matplotlib from complaining because of too many figures opened
    mpl.rcParams['figure.max_open_warning'] = 200 
    #thinner lines in general
    mpl.rcParams['axes.linewidth'] = 0.3
    # Hi def figure
    mpl.rcParams['figure.dpi'] = 600 


    # dimensions for figure panels and spaces
    # all sizes are inches for consistency with matplotlib
    ratio = .8
    fig_w = 10           # Width of figure
    fig_h = 10           # Height of figure
    rec_w = 8.             # Horizontal size of a panel
    rec_h = ratio * rec_w  # Vertical size of a panel
    sp_w = 2.5              # horizontal space between panels
    sp_h = .8              # vertical space between panels
    fig = plt.figure(figsize=(fig_w,fig_h))
    xp = .02               #coords of title (axes normalized coordinates)
    yp = 1.02
    #coords for the closeup  that is overlayed 
    x0 = 1.5/rec_w          #x-coord of bottom left position of closeup (axes coords)
    y0 = 1./rec_h          #y-coord of bottom left position of closeup (axes coords)
    dx = .4                #x-size of closeup axes (fraction of a "regular" panel)
    dy = .4                #y-size of closeup axes (fraction of a "regular" panel)
    #normalize sizes to obtain figure coordinates (0-1 both horizontally and vertically)
    rec_w = rec_w / fig_w
    rec_h = rec_h / fig_h
    sp_w  = sp_w  / fig_w
    sp_h  = sp_h  / fig_h

    pos = [x0, y0, rec_w, rec_h]
    ax = fig.add_axes(pos)

    ax.set_xlim([2000., 5.])   # "dum =" to avoid printing output
    ax.set_xscale('log')
    ax.set_ylim([1e-10, 1e2])
    ax.set_yscale('log')
    ax.set_xlabel('Wavelength [km]')
    ax.set_ylabel('Variance [dBZ^2]')

    ax.plot(mean_wavelength, mean_power)
    ax.scatter(mean_wavelength, mean_power)

    #ticks  = [-1.,0.,1.]        #tick values
    #dum = ax.set_xticks(ticks)
    #dum = ax.set_yticks(ticks)

    pic_dir = '/space/hall3/sitestore/eccc/mrd/rpndat/dja001/python_figures/'
    svg_name = pic_dir + 'dct_develop.svg'
    plt.savefig(svg_name)
    plt.close(fig)

    #hack svf for Latin Modern font
    d_py.lmroman(svg_name)

    #convert to svg if desired
    #d_py.convert(svg_name,'gif', del_orig=True, density=300, geometry='50%')
    #d_py.convert(svg_name,'jpg', del_orig=True, density=300, geometry='50%')
    #not sure what is accumulating but adding this garbage collection step 
    #prevents jobs from aborting when a largen number of files are made 
    gc.collect()
    print('done with: ', svg_name)




if __name__ == '__main__':
    main()

