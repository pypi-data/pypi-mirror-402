class InstAccum:
    
    def __init__(self, name=None, 
                       quantity=None, 
                       accum_dt=None, 
                       data_dir=None, 
                       data_dt=None, 
                       data_recipe=None,
                       median_filt=None, 
                       smooth_radius=None):
        """Use get_instantaneous or get_accuulations to read radar data from various sources

        args:
            data_dir:  [str]  /basse/dir/where/data/is/
            accum_dt:     [minutes] time during which accumulations are desired
            prefixt:   [strftime format] restrict search to files with this format

            Quantity is specified in general parameters and added to every reader's argument list
        """
        import numpy as np
        from gridded_obs.verify import _setup_logging

        self.logger = _setup_logging()

        self.logger.info('initializing "InstAccum" reader')

        if name is not None:
            self.name  = name
        else:
            raise ValueError('keyword "name" must be speficied')

        if quantity is not None:
            self.quantity  = quantity
        else:
            raise ValueError('keyword "quantity" must be speficied')

        if accum_dt is not None:
            self.accum_dt  = float(accum_dt)
        else:
            self.accum_dt  = None

        if data_dt is not None:
            self.data_dt  = float(data_dt)
        else:
            self.data_dt  = None

        if data_dir is not None:
            self.data_dir  = data_dir
        else:
            raise ValueError('keyword "data_dir" must be speficied')
        if data_recipe is not None:
            self.data_recipe  = data_recipe
        else:
            raise ValueError('keyword "data_recipe" must be speficied')

        if median_filt is not None:
            self.median_filt = float(median_filt)
        else:
            self.median_filt = None

        if smooth_radius is not None:
            self.smooth_radius = float(smooth_radius)
        else:
            self.smooth_radius = None

        #by default, data is returned on native grid
        #if needed, these variables are initialized after argument parsing in verify.py
        self.dest_lat = None
        self.dest_lon = None
    
    def interp_init(self, src_lat, src_lon, dest_lat, dest_lon):
        #for this reader, interpolation is performed by radar_tools functions

        #specifying these variables will trigger interpolation
        self.dest_lat = dest_lat
        self.dest_lon = dest_lon


    def get_data(self, validity_date, leadtime=None):
        """Read precip_rates and build precip accumulations from various sources

        args:
            validity_date:  [datetime object]  date at which data is desired
            leadtime:       [datetime timedelta object]  offset with respect to validity time

        """
        import datetime
        import numpy as np
        import domcmc.fst_tools 
        import domutils.radar_tools as radar_tools

        #take leadtime into account
        if leadtime is None:
            end_date = validity_date
        else:
            end_date = validity_date + leadtime

        if self.quantity == 'precip_rate':
            dat_dict = radar_tools.get_instantaneous(valid_date=end_date, 
                                                     data_path=self.data_dir, 
                                                     data_recipe=self.data_recipe, 
                                                     desired_quantity=self.quantity, 
                                                     latlon=True, 
                                                     dest_lon=self.dest_lon, 
                                                     dest_lat=self.dest_lat, 
                                                     median_filt=self.median_filt, 
                                                     smooth_radius=self.smooth_radius, 
                                                     odim_latlon_file=None )
        elif self.quantity == 'accumulation':
            dat_dict = radar_tools.get_accumulation(end_date=end_date,
                                                    duration=self.accum_dt,
                                                    data_path=self.data_dir,
                                                    data_recipe=self.data_recipe,
                                                    input_dt = self.data_dt, 
                                                    latlon=True,
                                                    dest_lat=self.dest_lat,
                                                    dest_lon=self.dest_lon,
                                                    median_filt=self.median_filt,
                                                    smooth_radius=self.smooth_radius, 
                                                    allow_missing_inputs=True,
                                                    logger=self.logger)
        else:
            raise ValueError('Only "precip_rate" and "accumulation" supported')

            #make sure qi min is 0.
            if dat_dict is not None :
                dat_dict['total_quality_index'] = np.where(dat_dict['total_quality_index'] <= 0., 0., dat_dict['total_quality_index'])


        if dat_dict is None :
            return None
        else:
            return {'values':dat_dict[self.quantity],
                    'qi_values':dat_dict['total_quality_index'],
                    'lats':dat_dict['latitudes'], 
                    'lons':dat_dict['longitudes']}
