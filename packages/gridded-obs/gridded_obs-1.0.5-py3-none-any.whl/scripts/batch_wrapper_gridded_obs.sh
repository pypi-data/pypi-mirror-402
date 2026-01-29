
#!/bin/bash

#wrapper that sets environment when submitting in batch mode
. ~/.profile

#SSMs
echo "loading rpn lib "
. r.load.dot rpn/libs/19.6.0
echo 'loading rpnpy SSMs ...'
echo 'compiler'
. ssmuse-sh -x comm/eccc/all/opt/intelcomp/intelpsxe-cluster-19.0.3.199
echo 'vgrid'
. r.load.dot /fs/ssm/eccc/mrd/rpn/vgrid/6.4.5 
echo "RPN PY"
. ssmuse-sh -d eccc/mrd/rpn/MIG/ENV/rpnpy/2.1.0

#load conda environment (for python), activate it and make a local link to conda python interpreter
eval "$(/home/ords/mrd/rpndat/dja001/python_miniconda3/bin/conda shell.bash hook)"
#conda activate gridded_obs
conda activate domutils_dev

##launch script for gridded obs
cd /home/dja001/python/gridded_obs/scripts/
./verif_N2FC80E19V1_30m.sh
#./launch_verification.sh

##launch script for gridded obs
#cd /home/dja001/python/lhn_2.5
#./verif_L16MIG8_30m.sh
