#!/bin/bash
#
# job time, change for what your job requires
#SBATCH -t 1:00:00
#
#SBATCH -p fujitsu
#
# job name
#SBATCH -J auto_ptycho
#

#SBATCH --exclusive
#SBATCH -N 1
#SBATCH --ntasks-per-core=1

# filenames stdout and stderr - customise, include %j
#SBATCH -o process_%j.out
#SBATCH -e process_%j.err

# load the modules required for you program - customise for your program
source /data/visitors/nanomax/common/sw/source_me_for_ptypy
mpiexec -N 24 python reconstruct.py $1

