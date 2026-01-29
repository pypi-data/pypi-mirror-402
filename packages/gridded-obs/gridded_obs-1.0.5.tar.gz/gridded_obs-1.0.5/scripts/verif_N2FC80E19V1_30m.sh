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
                      --date_0 '2019070100'                    \
                      --date_f '2019082600'                    \
                      --delta_date 720                         \
                      --leadtime_0 -180                        \
                      --leadtime_f 730                         \
                      --delta_leadtime   30                    \
                      --grid_dx   2.5                          \
                      --score_dir  '/space/hall3/sitestore/eccc/mrd/rpndat/dja001/dasVerif/ominusp/' \
                      --outname_file_struc '%verified_name/%Y%m%d%H_sqlite/%verified_name_vs_%reference_name__%Y%m%d%H.sqlite3' \
                      --figure_dir '/space/hall3/sitestore/eccc/mrd/rpndat/dja001/test_new_griddedobs_tmp/' \
                      --img_dt  10                             \
                      --verif_domains 'radars'                 \
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
                                                               \
                      --reference_reader  'BuildAccum'         \
                      --reference_name 'bmosaicsv81hacc'       \
                      --reference_accum_dt 30.                 \
                      --reference_data_dir '/space/hall4/sitestore/eccc/mrd/rpndat/dja001/obsProcess_fst/hrdps_sm4_me3_ete2019/' \
                      --reference_data_recipe '%Y%m%d%H%M_mosaic.fst' \
                                                               \
                      --verified_reader 'ModelPrDiff'          \
                      --verified_name 'N2FC80E19V1'            \
                      --verified_pr_dt 30                      \
                      --verified_data_dir '/space/hall3/sitestore/eccc/mrd/rpndat/dja001/maestro_archives/N2FC80E19V1_links/' \
                      --verified_prefix '%Y%m%d%H'             \




