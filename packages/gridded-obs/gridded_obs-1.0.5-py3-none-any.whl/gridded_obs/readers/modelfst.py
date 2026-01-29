
class ModelFst:
    def __init__(self, name=None, 
                       data_dir=None, 
                       file_struc=None, 
                       prefix=None,
                       quantity=None,
                       accum_dt=None,
                       varname=None, qi_varname=None, 
                       average=None, smooth_radius=None):
        """reader for CMC 'standard' files

        args:
            data_dir:      [str]  /basse/dir/where/data/is/
            file_struc:    [strftime format]  how to construct filename from date
            varname:       [str] Name of variable to read in standard file
        """

        import numpy as np
        from gridded_obs.verify import _setup_logging

        self.logger = _setup_logging()

        self.logger.info('initializing "ModelFst" reader')

        if name is not None:
            self.name  = name
        else:
            raise ValueError('keyword "name" must be speficied')

        if data_dir is not None:
            self.data_dir  = data_dir
        else:
            raise ValueError('keyword "data_dir" must be speficied')

        if varname is not None:
            self.varname  = varname
        else:
            self.varname = None

        if smooth_radius is not None:
            #maybe a string = 'None'
            if smooth_radius =='None':
                self.smooth_radius = None
            else:
                self.smooth_radius = float(smooth_radius)
        else:
            self.smooth_radius = None

        if average is not None:
            self.average = float(average)
        else:
            self.average = None

        if accum_dt is not None:
            self.accum_dt = float(accum_dt)
        else:
            self.accum_dt = None

        #optionnal variable
        self.file_struc  = file_struc
        self.qi_varname = qi_varname
        self.quantity   = quantity
        self.prefix  = prefix

        #by default, data is returned on native grid
        # if needed, these variables are initialized after argument parsing in verify.py
        # bt calling interp_init
        self.dest_lat = None
        self.dest_lon = None
        self.missing=-9999.

    def interp_init(self, src_lat, src_lon, dest_lat, dest_lon):

        import domutils.geo_tools as geo_tools

        self.dest_lat = dest_lat
        self.dest_lon = dest_lon
        #init interpolator
        self.proj_obj = geo_tools.ProjInds( src_lon=src_lon, src_lat=src_lat,
                                           dest_lon=dest_lon,   dest_lat=dest_lat,
                                           average=self.average, smooth_radius=self.smooth_radius,
                                           missing=self.missing)


    def get_data(self, validity_date, leadtime=None):
        """read data from a standard file

        args:
            validity_date:  [datetime object]  date at which data is desired
            leadtime:       [datetime timedelta object]  offset with respect to validity time

        """

        import domcmc.fst_tools 
        import numpy as np
        import datetime

        #take leadtime into account
        if leadtime is None:
            this_date = validity_date
        else:
            this_date = validity_date + leadtime

        if self.prefix is not None:
            prefix = validity_date.strftime(self.prefix)

        #read fst file for desired variable
        if self.quantity == 'accum_one_pr':
            #
            #
            #we are getting an pre-computed accumulation in a PR file 

            #precipitation at validity date
            pr_dict   = domcmc.fst_tools.get_data(dir_name=self.data_dir, var_name='PR', prefix=prefix, datev=this_date, latlon=True)

            if (pr_dict is None) :
                return None
            else:
                #forecast accumulation rate in mm
                #       *1000   -> conversion from meters to mm
                accumulation = (pr_dict['values'])*1000. 
                
                #output mimics output structure of fst_tools.get_data
                data_dict = {'values':accumulation,
                             'lat':pr_dict['lat'], 
                             'lon':pr_dict['lon'] }

        elif self.quantity == 'accumulation' or self.quantity == 'precip_rate':

            if self.varname == 'PR' :
                #we are getting precip from the difference of PR at two times

                #precipitation at validity date
                pr_t_dict   = domcmc.fst_tools.get_data(dir_name=self.data_dir, var_name='PR', prefix=prefix, datev=this_date, latlon=True)

                #get precipitation accumulation at validity date - accum_dt
                deltat = self.accum_dt*60. #convert minutes to seconds
                date_mdt = this_date - datetime.timedelta(seconds=deltat)
                pr_mdt_dict = domcmc.fst_tools.get_data(dir_name=self.data_dir, var_name='PR', prefix=prefix, datev=date_mdt)
        
                if (pr_t_dict is None) or (pr_mdt_dict is None):
                    return None
                else:
                    #forecast accumulation rate in mm
                    #       *1000   -> conversion from meters to mm
                    accumulation = (pr_t_dict['values'] - pr_mdt_dict['values'])*1000. 

                    if self.quantity == 'accumulation':

                        data_dict = {'values':accumulation,
                                     'lat':pr_t_dict['lat'], 
                                     'lon':pr_t_dict['lon'] }

                    elif self.quantity == 'precip_rate':
                        #forecast precip rate in mm/h
                        #       *3600   -> for precip rate during one hour
                        #       /deltat -> time difference between the two accumulation (PR) values that were read
                        precip_rate = accumulation*3600./deltat

                        data_dict = {'values':precip_rate,
                                     'lat':pr_t_dict['lat'], 
                                     'lon':pr_t_dict['lon'] }

            else:
                #
                #
                #read single entry in fst file
                if self.file_struc is not None:
                    this_file = self.data_dir + this_date.strftime(self.file_struc)
                    data_dict = domcmc.fst_tools.get_data(file_name=this_file, var_name=self.varname, datev=this_date, latlon=True)
                else: 
                    data_dict = domcmc.fst_tools.get_data(dir_name=self.data_dir, prefix=prefix, var_name=self.varname, datev=this_date, latlon=True)

        #stop here if found nothing
        if data_dict is None:
            return None

        #some variables need conversion
        if self.varname == 'RT' and self.quantity == 'precip_rate':
            #m/s to mm/h ( * 1000 * 3600 )
            data_dict['values'] *= 3.6e6

        #get quality index 
        if self.qi_varname is not None:
            qi_dict = domcmc.fst_tools.get_data(file_name=this_file, var_name=self.qi_varname, datev=this_date)
            if qi_dict is not None:
                qi_values = qi_dict['values']
            else:
                qi_values = None
        else:
            qi_values = None

        #interpolation is needed
        if self.dest_lat is not None and self.dest_lon is not None:
            out_lat = self.dest_lat
            out_lon = self.dest_lon

            if self.average or self.smooth_radius is not None:
                #interpolation involving some averaging
                if qi_values is not None:
                    #weighted average
                    out_val, out_qi = self.proj_obj.project_data(data_dict['values'],
                                                                 weights=qi_values,
                                                                 output_avg_weights=True)
                else:
                    out_qi  = None
                    out_val = self.proj_obj.project_data(data_dict['values'])
            else:
                if qi_values is not None:
                    out_qi = self.proj_obj.project_data(qi_values)
                else:
                    out_qi = None
                out_val = self.proj_obj.project_data(data_dict['values'])

        else:
            #no interpolation, output on native grid
            out_val = data_dict['values']
            out_qi  = qi_values
            out_lat = data_dict['lat']
            out_lon = data_dict['lon']



        return {'values':out_val, 
                'qi_values':out_qi,
                'lats':out_lat, 
                'lons':out_lon}

