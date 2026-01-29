
export XDG_RUNTIME_DIR=/space/hall3/sitestore/eccc/mrd/rpndat/dja001/tmpdir
export MPLBACKEND="agg" 
ulimit -s 128000

#make sure numpy does not use multithreading 
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1   
