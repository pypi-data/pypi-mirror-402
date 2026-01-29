#!/bin/bash 


#These system variables are important for preventing crashes when running in parallel (n_cpus > 1)
export XDG_RUNTIME_DIR=/space/hall3/sitestore/eccc/mrd/rpndat/dja001/tmpdir
export MPLBACKEND="agg" 
ulimit -s 128000
#make sure numpy does not use multithreading 
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1   

#type :
#   python gridded_obs.py -h 
#for a complete description of arguments
python -c 'import gridded_obs; gridded_obs.verify()'           \
                      --date_0 '2022020100'                    \
                      --date_f '2022020100'                    \
                      --delta_date 720                         \
                      --leadtime_0 -180                        \
                      --leadtime_f 730                         \
                      --delta_leadtime   10                    \
                      --grid_dx   2.5                          \
                      --score_dir  '/space/hall5/sitestore/eccc/mrd/rpndat/dja001/gridded_obs/ominusp/' \
                      --outname_file_struc '%verified_name/%Y%m%d%H_sqlite/%verified_name_vs_%reference_name__%Y%m%d%H.sqlite3' \
                      --figure_dir '/space/hall5/sitestore/eccc/mrd/rpndat/dja001/gridded_obs/figures/%verified_name/' \
                      --img_dt  60                             \
                      --verif_domains 'radar2p5km'             \
                      --thresholds  .1 .5 1. 5. 10.            \
                      --k_nbins 100                            \
                      --min_qi  0.2                            \
                      --hist_nbins 100                         \
                      --hist_min 0.01                          \
                      --hist_max 100.                          \
                      --hist_log_scale True                    \
                      --lmin_range 2.5 2000                    \
                      --n_cpus 40                              \
                      --complete_mode 'clobber'                \
                      --quantity 'precip_rate'                 \
                                                               \
                      --reference_reader  'InstAccum'          \
                      --reference_name 'bmosaicsv8'            \
                      --reference_data_dir '/space/hall6/sitestore/eccc/mrd/rpndat/dja001/maestro_archives/N2810FS22V1/banco/obsprocess/' \
                      --reference_data_recipe '%Y%m%d%H_%M_mosaic.fst' \
                                                               \
                      --verified_reader 'ModelFst'             \
                      --verified_name 'cycled_correct_v6'      \
                      --verified_varname 'PR'                  \
                      --verified_accum_dt 10                   \
                      --verified_data_dir '/space/hall5/sitestore/eccc/mrd/rpndat/dja001/maestro_archives/cycled_correct_v6/gridpt/prog/hyb/' \
                      --verified_prefix '%Y%m%d%H'             \
