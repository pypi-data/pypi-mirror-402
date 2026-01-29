class Handler():
    '''Handling sqlite files from gridded obs
    '''

    def connect(self, must_exist=False, none_for_nonexistent=False, create=False):
        """connect to db with different behavior if file does not already exist

        args:
        must_exist:           if True, an error is thrown if file does not exist
        none_for_nonexistent: if True, return None        if file does not exist
        create:               if True, file is created
        """
        import os
        import sqlite3
        import warnings

        if not os.path.isfile(self.sqlite_file):
            if must_exist:
                raise RuntimeError('File: '+self.sqlite_file+ '  does not exists')

            #return None if file does not exists
            if none_for_nonexistent:
                warnings.warn('File: '+self.sqlite_file+ '  does not exists; returning None')
                return None

            if create:
                #do nothing, file is created automatically
                pass

        try:
            conn = sqlite3.connect(self.sqlite_file, timeout=30.0)
        except:
            raise RuntimeError('Problem connecting to sqlite file:'+self.sqlite_file)

        return conn

    def make_filename(self, params, date):
        """return sql filename for two experiments being compared
        """

        import os

        #replace '%verified_name'  with the verified  experiment name
        #replace '%reference_name' with the reference experiment name
        outname = params.outname_file_struc.replace('%verified_name', self.verified_name).replace('%reference_name', self.reference_name)

        #put date in output name
        outname = date.strftime(outname)

        return os.path.join(params.score_dir, outname)


    def get_dctpow_centers(self,c):
        """get wavelengths for dct power spectra
        """
        import numpy as np
        cmd = '''select center from dctpow_bin_centers ;'''
        c.execute(cmd)
        entries = c.fetchall()
        centers = np.full(len(entries), np.nan)
        for ii, entry in enumerate(entries):
            centers[ii] = entry[0]
        return centers
    
    def get_hist_bin_edges(self,c):
        """get edges of histograms in file
        """
        import numpy as np
        cmd = '''select edge from hist_bin_edges ;'''
        c.execute(cmd)
        entries = c.fetchall()
        edges = np.full(len(entries), np.nan)
        for ii, entry in enumerate(entries):
            edges[ii] = entry[0]
        return edges
    
    def get_domain_id(self, c,domain_name):
        """get domain id
        """
        import warnings
    
        cmd = 'select id from domains where (dname = \''+domain_name+'\');'
        try:
            c.execute(cmd)
            domain_id = c.fetchall()
            if len(domain_id) == 0:
                warnings.warn(f'problem getting domain_id in file: {self.sqlite_file} for domain: {domain_name}, returning None')
                return None
            else:
                if len(domain_id) > 1:
                    warnings.warn('more than one value returned for domain_id in '+self.sqlite_file+ 'returning None')
                    return None

                #this is the domain id that we want
                return domain_id[0][0]
    
        except:
            warnings.warn('problem getting domain_id in '+self.sqlite_file+ 'returning None')
            return None
    
    def get_threshold_id(self, c, threshold):
        """get threshold id
        """

        import warnings

        small = 1e-6
    
        low  = '{:10.6f}'.format(threshold - small)
        high = '{:10.6f}'.format(threshold + small)
        cmd = 'select id from thresholds where (value > '+low+' and value < '+high+');'
        try:
            c.execute(cmd)
            threshold_id = c.fetchall()
            if len(threshold_id) == 0:
                warnings.warn('problem getting threshold_id in '+self.sqlite_file+ 'returning None')
                return None
            else:
                if len(threshold_id) > 1:
                    warnings.warn('more than one value returned for threshold_id in '+self.sqlite_file+ 'returning None')
                    return None

                #this is the threshold id we are looking for
                return threshold_id[0][0]
    
        except:
            warnings.warn('problem getting threshold_id in '+self.sqlite_file+ 'returning None')
            return None

    def strings_from_floats(self, hist_bin_edges, str_type=None, remove_last=True):
        """make strings for histogram columns

        allows to create the columns, update the data and read it with select
        """

        #TODO This code actually picks row id for bin edges/centers
        #     this should be more explicit

        if str_type is None:
            raise ValueError('need to define a type of string desired')
        elif str_type == 'create':
            suffix = ' real, '
        elif str_type == 'update':
            suffix = '=? , '
        elif str_type == 'select':
            suffix = ', '
        else:
            raise ValueError('unknown str_type')

        #make the string
        out_str = ''
        if remove_last:
            iter_list = hist_bin_edges[:-1]
        else:
            iter_list = hist_bin_edges

        for ii, emin in enumerate(iter_list):
            out_str += ('h_{:05d}'+suffix).format(ii)

        #the -2 here removes the last space and comma
        return out_str[:-2]

    def exec_wait(self, c, cmd, arg=None):
        '''exec commands in a loop to mitigate "database is locked" errors

        TODO: This is probably not the best way to handle this, 
        '''
        import time
        import random
        max_iter = 10
        ii = 0
        while ii <= max_iter:

            try:
                #run command and return if sucess
                c.execute(cmd, arg)
                return 
            except:
                print('wait a little!! iteration:', ii)
                time.sleep( random.uniform(0., 10.) )

            ii += 1

        #if code gets here, command did not run
        raise RuntimeError('Could not run'+cmd+ 'in '+str(max_iter)+' tries')



    def get_element_id(self, c, table_name=None, domain_id=None, leadtime_minutes=None, threshold_id=None, create=False):
        '''check if the line we want to fill already exists in a given sql table
        '''


        if table_name is None:
            raise ValueError('table name is mandatory')

        if domain_id is None:
            raise ValueError('domain_id is mandatory')

        if leadtime_minutes is None:
            raise ValueError('leadtime_minutes is mandatory')

        if threshold_id is None:
            cmd = '''select id from '''+table_name+''' where (leadtime_minutes = '''+str(leadtime_minutes)+'''
                                                              and domain_id    = '''+str(domain_id)+');'
        else:
            cmd = '''select id from '''+table_name+''' where (leadtime_minutes = '''+str(leadtime_minutes)+'''
                                                              and domain_id    = '''+str(domain_id)+'''
                                                              and threshold_id = '''+str(threshold_id)+');'
        #self.exec_wait(c, cmd)

        c.execute(cmd)
        d_id = c.fetchall()

        if len(d_id) == 0:
            if create:
                #line does not exist, create it and keep track of id
                if threshold_id is None:
                    cmd = '''insert into '''+table_name+''' (leadtime_minutes, domain_id) VALUES(?,?) ;'''
                    self.exec_wait(c, cmd, (leadtime_minutes, domain_id))
                else:
                    cmd = '''insert into '''+table_name+''' (leadtime_minutes, domain_id, threshold_id) VALUES(?,?,?) ;'''
                    self.exec_wait(c, cmd, (leadtime_minutes, domain_id, threshold_id))
                d_id = c.lastrowid
                already_existed = False
            else:
                #element not there
                d_id = None
                already_existed = False

        else:
            if len(d_id) > 1:
                raise ValueError('more than one value returned for id in histogram table ')
            d_id = d_id[0][0]
            already_existed = True

        return d_id, already_existed
    


    def dctpow_bins(self, c, centers, params):
        """create or check dcpow_bin tables if needed
        """

        import numpy as np

        #if table exists, 
        cmd = ''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='dctpow_bin_centers' '''
        c.execute(cmd)
        res = c.fetchone()[0]
        if res == 1:
            # there is a table named "dctpow_bin_centers"
            cmd = 'select center from dctpow_bin_centers'
            c.execute(cmd)
            centers_already_in_table = c.fetchall()
            #sql output needs to be reshaped to match numpy array
            if not np.allclose(centers, np.array(centers_already_in_table, dtype=float).ravel(), equal_nan=True):
                print('those we had')
                print(centers)
                print('those we now have')
                print(np.array(centers_already_in_table, dtype=float).ravel())
                print('is close test')
                print(np.isclose(centers, np.array(centers_already_in_table, dtype=float).ravel(), equal_nan=True))
                raise ValueError('dctpow_bin_centers differ from those already in file')
        else:
            # there are no tables named "dctpow_bin_centers"

            cmd = '''create table dctpow_bin_centers(id  integer primary key, center real );'''
            c.execute(cmd)
        
            cmd = '''insert into dctpow_bin_centers (center) VALUES (?);'''
            for center in centers:
                c.execute(cmd, (center,))

            #string column names from bin centers
            dctpow_col_str = self.strings_from_floats(centers, str_type='create', remove_last=False)
            #make power spectra tables
            # 1- first a table for dct pow spectra from the reference dataset
            cmd = '''create table if not exists dctpow_reference(id  integer primary key, 
                                                                 leadtime_minutes integer, 
                                                                 domain_id        integer,
                                                                 '''+dctpow_col_str+');'
            c.execute(cmd)
            # 2- a table for dct pow spectra from the verified dataset
            cmd = '''create table if not exists dctpow_verified( id  integer primary key, 
                                                                 leadtime_minutes integer, 
                                                                 domain_id        integer,
                                                                 '''+dctpow_col_str+');'
            c.execute(cmd)


    def insert_hist(self, c, table_name, element_id, histogram ,params):
        """insert histogram counts in a given histogram table
        """
    
        #insert data in table
        h_col_update_str = self.strings_from_floats(params.hist_bin_edges, str_type='update')
        cmd = '''update '''+table_name+''' set '''+h_col_update_str+'''  where (id = '''+str(element_id)+'''); '''
        h_tuple = tuple([float(val) for val in histogram])  #conversion to float to make sqlite3 happy
        c.execute(cmd,h_tuple)

    def insert_dctpow(self, c, table_name, element_id, 
                               bin_centers, powers):
        """insert dct power spectra in given table
        """
    
        #insert data in table
        col_update_str = self.strings_from_floats(bin_centers, str_type='update', remove_last=False)
        cmd = '''update '''+table_name+''' set '''+col_update_str+'''  where (id = '''+str(element_id)+'''); '''
        p_tuple = tuple([float(val) for val in powers])  #conversion to float to make sqlite3 happy
        c.execute(cmd,p_tuple)

    def get_hist_values(self, c, table_name, leadtime_minutes, domain_id, hist_bin_edges, hist_string):
        """read histogram counts in a given histogram table
        """
        import numpy as np
    
        #id of element we need
        element_id, is_there = self.get_element_id(c, table_name=table_name, domain_id=domain_id, leadtime_minutes=leadtime_minutes)
        if is_there:
            #read data in table
            cmd = '''select '''+hist_string+''' from '''+table_name+'''  where (id = '''+str(element_id)+'''); '''
            c.execute(cmd)
            entries = np.array(c.fetchall()[0])
            return entries 
        else:
            #no histogram at desired leadtime
            return None

    def get_dctpow_values(self, c, table_name, leadtime_minutes, domain_id, dctpow_centers, dctpow_string):
        """read dct power values
        """
        import numpy as np
    
        #id of element we need
        element_id, is_there = self.get_element_id(c, table_name=table_name, domain_id=domain_id, leadtime_minutes=leadtime_minutes)
        if is_there:
            #read data in table
            cmd = '''select '''+dctpow_string+''' from '''+table_name+'''  where (id = '''+str(element_id)+'''); '''
            c.execute(cmd)
            entries = np.array(c.fetchall()[0])
            return entries 
        else:
            #no dct power spectra at desired leadtime
            return None

    def populate_id_dict(self, c, params):
        '''return dictionary of domains:domain_id and threshold:threshold_id
        '''

        #for domains
        domain_id_dict = {}
        for domain in params.verif_domains:
            #id element for the domain being veridied
            domain_id = self.get_domain_id(c,domain)
            if domain_id is None:
                raise ValueError('Problem populatinf domain_ids dictionary')
            domain_id_dict[domain] = domain_id
        self.domain_id_dict = domain_id_dict
    

        threshold_id_dict = {}
        for threshold in params.thresholds:
            #id element for the threshold being veridied
            threshold_id = self.get_threshold_id(c,threshold)
            if threshold_id is None:
                raise ValueError('Problem populatinf domain_ids dictionary')
            threshold_id_dict[str(threshold)] = threshold_id
        self.threshold_id_dict = threshold_id_dict
    


    def found_entries_at_leadtime(self, leadtime_minutes):
        """ Returne True if entries are found
            in sqlite file at a desired leadtime
        """
        try:
            conn = self.connect(create=False) 
        except:
            #could not open sqlite file, possibly corrupted
            conn = None

        if conn is None:
            return False

        c = conn.cursor()
        
        #
        #make info table
        c.execute('select leadtime_minutes from stats;')
        entries = c.fetchall()
        conn.close()

        #entries are of the form:
        #[(-170,), (-170,), (-170,), (-170,), (-170,), (-160,), (-160,), (-160,), (-160,), (-160,), (-150,), (-150,), (-150,), (-150,), ... ]

        combined_set = set(entries)  & set( [(leadtime_minutes,)] )
        if len(combined_set) > 0:
            # there is at least one corresponding leadtime in file
            return True
        else:
            # set is empty, this leadtime does not exist in file
            return False

    def init_sqlite_file(self, params):

        '''#initialize sql tables that will contain the data

        Also handles whether a date will be verified or not tdepending on params.complete_mode

        '''

        import sqlite3
        import os
        import glob
        import numpy as np
        import domutils._py_tools as py_tools
        import gridded_obs


        
        # if sqlite file already exists, we stop here and return here
        if self.sqlite_file_exists():
            return

        #make dir if it does not already exists
        py_tools.parallel_mkdir(os.path.dirname(self.sqlite_file))

        conn = self.connect(create=True) 
        c = conn.cursor()
        
        #
        #make info table
        cmd = '''create table if not exists info(id                integer primary key, 
                                                 reference_name    text,
                                                 verified_name     text,
                                                 quantity          text,
                                                 verif_hash        text,
                                                 min_qi            real,
                                                 grid_dx           real );'''
        c.execute(cmd)
        cmd = '''insert into info (reference_name,
                                   verified_name ,
                                   quantity,
                                   min_qi,
                                   grid_dx ) VALUES (?,?,?,?,?);'''
        c.execute(cmd, (params.reference_reader.name, 
                        params.verified_reader.name, 
                        params.quantity,
                        params.min_qi, 
                        params.grid_dx))
        
        #
        #make threshold table
        cmd = '''create table if not exists thresholds(id    integer primary key, 
                                                       value real);'''
        c.execute(cmd)
        cmd = '''insert into thresholds (value) VALUES (?)'''
        for threshold in params.thresholds:
            c.execute(cmd, (threshold,))
        
        #
        #make domains table
        cmd = '''create table if not exists domains(id    integer primary key, 
                                                    dname text);'''
        c.execute(cmd)
        cmd = '''insert into domains (dname) VALUES (?);'''
        for domain in params.verif_domains:
            c.execute(cmd, (domain,))
        
        #
        #make histograms tables
        #
        # first a table for bin edges values
        cmd = '''create table if not exists hist_bin_edges(id  integer primary key, 
                                                           edge real );'''
        c.execute(cmd)
        cmd = '''insert into hist_bin_edges (edge) VALUES (?);'''
        for edge in params.hist_bin_edges:
            c.execute(cmd, (edge,))

        # second a table for histograms from the reference dataset
        h_col_create_str = self.strings_from_floats(params.hist_bin_edges, str_type='create')
        #table for reference histograms
        cmd = '''create table if not exists hist_reference(id  integer primary key, 
                                                           leadtime_minutes integer, 
                                                           domain_id        integer,
                                                           '''+h_col_create_str+');'
        c.execute(cmd)
        #
        # third a table for histograms from the verified dataset
        cmd = '''create table if not exists hist_verified( id  integer primary key, 
                                                           leadtime_minutes integer, 
                                                           domain_id        integer,
                                                           '''+h_col_create_str+');'
        c.execute(cmd)

        #
        #make dctpow tables
        #   wavelength and power depend on domain size
        for (domain_name, [x0,y0,xf,yf]) in params.domain_dict.items():
            nx = xf - x0
            ny = yf - y0
            dummy = np.ones([nx, ny])
            (wavenum, 
             wavelengths, 
             power) = gridded_obs.pow_dct(dummy, 
                                          dx_km=params.grid_dx, n_bands=params.k_nbins)
            #tables:
            #       dctpow_bin_centers
            #       dctpow_reference 
            #       dctpow_verified  
            #get created here since they don't already exist
            self.dctpow_bins(c, wavelengths, params)
        
        
        
        #
        #make stats table to be filled by processes
        cmd = '''create table if not exists stats(id  integer primary key, 
                                                  leadtime_minutes integer, 
                                                  threshold_id     integer,
                                                  domain_id        integer,
                                                  x                integer,
                                                  y                integer,
                                                  z                integer,
                                                  w                integer,
                                                  lmin             real,
                                                  corr_coeff       real );'''
        c.execute(cmd)

        
        conn.commit()
        conn.close()


    def aquire_lock(self):
        """ Acquire file lock
        """
        import time
        import os

        start_time = time.time()
        timeout = 120.
        delay   = .5
        while True:
            try:
                # Attempt to create the lockfile.
                # These flags cause os.open to raise an OSError if the file already exists.
                fd = os.open(self.date_lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                with os.fdopen(fd, "a") as f:
                    f.write('You shall not pass!')
                break
            except FileExistsError:
                if (time.time() - start_time) >= timeout:
                    raise RuntimeError("Timeout occurred getting file lock")
                print(self.date_lock_file)
                print('waiting lockfile')
                time.sleep(delay)

        return True


    def release_lock(self):
        import os
        if os.path.isfile(self.date_lock_file):
            os.unlink(self.date_lock_file)


    def sqlite_from_dict(self, params, pickle_dict, leadtime_minutes ):
        """write entry at leadtime_minutes to sqlite file

        if sqlite file does not exist for this date, it will be created

        the writing part alone takes less 0.02s to complete
        """

        # this function only returns when this process has the lockfile
        self.aquire_lock()

        # sqlite file needs to already exist before it is filled with scores
        # this is done here 
        # if file already exists, code just moves on
        self.init_sqlite_file(params)

        # open sqlite file
        conn = self.connect(must_exist=True)
        c = conn.cursor()

        # fill attributes containing domain and threshold dicts
        self.populate_id_dict(c, params)

        # iterate over verification domains
        for this_domain in pickle_dict.keys():

            #id element for the domain being verified
            domain_id = self.domain_id_dict[this_domain]

            #
            #
            # histograms
            #
            #reference data
            elem_id, already_existed = self.get_element_id(c, table_name='hist_reference', 
                                                              domain_id=domain_id, 
                                                              leadtime_minutes=leadtime_minutes, 
                                                              create=True)
            reference_hist = pickle_dict[this_domain]['reference_hist']
            self.insert_hist(c, 'hist_reference', elem_id, reference_hist, params)

            elem_id, already_existed = self.get_element_id(c, table_name='hist_verified', 
                                                              domain_id=domain_id, 
                                                              leadtime_minutes=leadtime_minutes,
                                                              create=True)
            verified_hist = pickle_dict[this_domain]['verified_hist']
            self.insert_hist(c, 'hist_verified', elem_id, verified_hist, params)

            #
            #
            # DCT power spectrum
            (elem_id, already_existed) = self.get_element_id(c, table_name='dctpow_reference', 
                                                                domain_id=domain_id, 
                                                                leadtime_minutes=leadtime_minutes, 
                                                                create=True)
            reference_wavelengths = pickle_dict[this_domain]['reference_wavelengths']
            self.dctpow_bins(c, reference_wavelengths, params)
            reference_power = pickle_dict[this_domain]['reference_power']
            self.insert_dctpow(c, 'dctpow_reference', elem_id, reference_wavelengths, reference_power)

            (elem_id, already_existed) = self.get_element_id(c, table_name='dctpow_verified', 
                                                                domain_id=domain_id, 
                                                                leadtime_minutes=leadtime_minutes,
                                                                create=True)
            verified_wavelengths = pickle_dict[this_domain]['verified_wavelengths']
            self.dctpow_bins(c, verified_wavelengths, params)
            verified_power = pickle_dict[this_domain]['verified_power']
            self.insert_dctpow(c, 'dctpow_verified', elem_id, verified_wavelengths, verified_power)

            conn.commit()

            # iterate over thresholds
            for th_key in pickle_dict[this_domain].keys():
                #keys starting with th_ are thresholds dict
                #we skip other entries
                if '_' in th_key:
                    vv = th_key.split('_')
                    if not vv[0] == 'th':
                        continue
                    else:
                        this_threshold = vv[1]
                else:
                    continue

                #id element for the threshold being veridied
                threshold_id = self.threshold_id_dict[str(this_threshold)]

                #a new row in sql table is created if it does not already exists
                elem_id, already_existed = self.get_element_id(c, table_name='stats', 
                                                                  domain_id=domain_id, 
                                                                  threshold_id=threshold_id, 
                                                                  leadtime_minutes=leadtime_minutes,
                                                                  create=True)
                #write x,y,z,w
                x = pickle_dict[this_domain][th_key]['x']
                y = pickle_dict[this_domain][th_key]['y']
                z = pickle_dict[this_domain][th_key]['z']
                w = pickle_dict[this_domain][th_key]['w']

                cmd = '''update stats set x = ? , y = ? , z = ? , w = ?  where (id = '''+str(elem_id)+'''); '''
                self.exec_wait(c, cmd, arg=(int(x),int(y),int(z),int(w)))

                #write correlation coefficient
                corr_coeff = pickle_dict[this_domain][th_key]['corr_coeff']
                cmd = '''update stats set corr_coeff = ? where (id = '''+str(elem_id)+'''); '''
                self.exec_wait(c, cmd, arg=(corr_coeff,))

                #write lmin
                lmin_value = pickle_dict[this_domain][th_key]['lmin_value']
                if lmin_value is not None:
                    cmd = '''update stats set lmin = ? where (id = '''+str(elem_id)+'''); '''
                    self.exec_wait(c, cmd, arg=(lmin_value,))
                
            conn.commit()


        #we are done writing to this file, release lock
        conn.close()
        self.release_lock()




    def sqlite_file_exists(self):
        """ Does sqlite file exists?
            return True or False
        """
        import os
        return os.path.isfile(self.sqlite_file)



    def __init__(self, date, params, verified_name=None):

        '''#initialize object that will handle sqlite files
        '''
        import os

        if hasattr(params, 'reference_name'):
            # in aggretation mode
            self.reference_name = params.reference_name
            if verified_name is None:
                raise ValueError('verified name must be provided during aggregation')
            else:
                self.verified_name = verified_name
        else:
            # this happens in verification mode 
            self.reference_name = params.reference_reader.name
            self.verified_name  = params.verified_reader.name


        #
        #
        #object attributes for later use
        sqlite_file = self.make_filename(params, date)

        self.sqlite_file = sqlite_file

        #lock file identifying this verification round
        self.date_lock_file = sqlite_file+'.lock'

        # make sure directory is there for lock file 
        lock_dir = os.path.dirname(self.date_lock_file)
        if not os.path.isdir(lock_dir):
            os.makedirs(lock_dir)


