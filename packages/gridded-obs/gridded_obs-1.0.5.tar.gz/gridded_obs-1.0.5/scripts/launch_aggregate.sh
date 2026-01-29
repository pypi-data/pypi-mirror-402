#!/bin/bash

#   colors can be specified as:
#   '(r,g,b)'     colors in the range 0-255
#   '(r,g,b,a)'   colors in the range 0-255  alpha in the range 0-1
#   'l_orange_0.7' for legs colors         0.0 for pale color, 1.0 for dark colors
#                  color can be one of 'brown','blue','green','orange', 'red','pink','purple','yellow', 'b_w'
#                  see: https://domutils.readthedocs.io/en/stable/legsTutorial.html#specifying-colors
#   
#   any other strings will be passed "as is" to matplotlib

#   linestyle: 'solid' 'dotted' 'dashed' 'dashdot'
#   passed "as is" to matplotlib "linestyle" argument of the ax.plot() method


#parameters for the aggregation
date_0='2022020100'       
date_f='2022022812'

delta_date=720
leadtime_0=-180
leadtime_f=730
delta_leadtime=10
leadtime_ignore=10
leadtime_greyed_out=(-180 180)
score_dir='/space/hall5/sitestore/eccc/mrd/rpndat/dja001/gridded_obs/ominusp/'
outname_file_struc='%verified_name/%Y%m%d%H_sqlite/%verified_name_vs_%reference_name__%Y%m%d%H.sqlite3'
figure_dir='/space/hall5/sitestore/eccc/mrd/rpndat/dja001/gridded_obs/figures/'
figure_format='svg'
verif_domains=('radar2p5km')
make_same=('False')
show_obs_num=('True')
thresholds=(.1 .5 1. 5. 10.)
time_series=('fbias' 'pod' 'far' 'csi' 'lmin' 'corr_coeff')
#time_series=('fbias' 'csi' 'lmin')
twod_panels=('dctpow' 'histograms')
twod_deltat=720
n_cpus=1

#
#
#Use those to force the Y range for time_series figures
# comment them for automatic range
#ylim_fbias=(0.92 1.75)
#ylim_pod=(0.18   .35)
#ylim_far=(0.75 0.88)
#ylim_csi=(0.08 0.16)
#ylim_lmin=(50. 250.)
#ylim_corr_coeff=(0.075 0.155)

#
#name of reference dataset
reference_name='bmosaicsv8'

#experiments being verified
exp_list=(       'cycled_correct_v6' )
exp_desc=(       'cycled_correct_v6' )
exp_color=(      'l_orange_0.7'      )
exp_linestyle=(  'solid'             )
exp_linewidth=(  '2.5'               )


## you can simultaneously plot multiple curves for different experiments
##experiments being verified
#exp_list=(       'N2820RC1IC4E19' 'N2FC80E19V3'   )
#exp_desc=(       'control'        'experiment_v3' )
#exp_color=(      'l_orange_0.7'   'l_blue_0.7'    )
#exp_linestyle=(  'solid'          'dashed'        )
#exp_linewidth=(  '2.5'            '2.5'           )





#
#
#Users should not have to change anything below this line
##########################################################

#These systrem variables are important for preventing crashes
export XDG_RUNTIME_DIR=/space/hall5/sitestore/eccc/mrd/rpndat/dja001/tmpdir
export MPLBACKEND="agg" 
ulimit -s 128000
#make sure numpy does not use multithreading 
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1   

#workaround the fact that argparse does not like arguments with no value
if [[ -z "${ylim_fbias}" ]]      ; then ylim_fbias=None; fi
if [[ -z "${ylim_pod}" ]]        ; then ylim_pod=None; fi
if [[ -z "${ylim_far}" ]]        ; then ylim_far=None; fi
if [[ -z "${ylim_csi}" ]]        ; then ylim_csi=None; fi
if [[ -z "${ylim_lmin}" ]]       ; then ylim_lmin=None; fi
if [[ -z "${ylim_corr_coeff}" ]] ; then ylim_corr_coeff=None; fi


#you can use :
#   python gridded_obs.py -h 
#for a complete description of arguments
python -c 'import gridded_obs; gridded_obs.aggregate()'               \
                    --date_0 ${date_0}                                \
                    --date_f ${date_f}                                \
                    --delta_date ${delta_date}                        \
                    --leadtime_0 ${leadtime_0}                        \
                    --leadtime_f ${leadtime_f}                        \
                    --delta_leadtime   ${delta_leadtime}              \
                    --leadtime_ignore  ${leadtime_ignore}             \
                    --leadtime_greyed_out  ${leadtime_greyed_out[*]}  \
                    --score_dir             ${score_dir}              \
                    --outname_file_struc ${outname_file_struc}        \
                    --figure_dir ${figure_dir}                        \
                    --figure_format ${figure_format}                  \
                    --verif_domains ${verif_domains[*]}               \
                    --make_same ${make_same}                          \
                    --show_obs_num ${show_obs_num}                    \
                    --thresholds  ${thresholds[*]}                    \
                                                                      \
                    --time_series  ${time_series[*]}                  \
                    --twod_panels  ${twod_panels[*]}                  \
                                                                      \
                    --n_cpus ${n_cpus}                                \
                                                                      \
                    --reference_name ${reference_name}                \
                                                                      \
                    --exp_list        ${exp_list[*]}                  \
                    --exp_desc        ${exp_desc[*]}                  \
                    --exp_color       ${exp_color[*]}                 \
                    --exp_linestyle   ${exp_linestyle[*]}             \
                    --exp_linewidth   ${exp_linewidth[*]}             \
                    --ylim_fbias      ${ylim_fbias[*]}                \
                    --ylim_pod        ${ylim_pod[*]}                  \
                    --ylim_far        ${ylim_far[*]}                  \
                    --ylim_csi        ${ylim_csi[*]}                  \
                    --ylim_lmin       ${ylim_lmin[*]}                 \
                    --ylim_corr_coeff ${ylim_corr_coeff[*]}           \

