#!/bin/bash
#SBATCH --job-name=af_predict
#SBATCH --output=/cellar/users/snwright/Data/SlurmOut/af_%A_%a.out
#SBATCH --error=/cellar/users/snwright/Data/SlurmOut/af_%A_%a.err
#SBATCH --partition=nrnb-gpu
#SBATCH --account=nrnb-gpu
#SBATCH --mem=16G
#SBACTH --cpus-per-task=4
#SBACTH -G 1
#SBATCH --array=1-20
#SBATCH --time=2-00:00:00

inputdir=/cellar/users/snwright/Git/AlphaPulldown/example_data
afdir=/cellar/users/snwright/Git/AlphaPulldown/alphapulldown

python -u $afdir/run_multimer_jobs.py --mode=pulldown \
--num_cycle=3 \
--num_predictions_per_model=1 \
--output_path=/cellar/users/snwright/Data/Network_Analysis/alphafold/mmseq/ \
--data_dir=/cellar/shared/alphafold/ \
--protein_lists=$inputdir/baits.txt,$inputdir/candidates_shorter.txt \
--monomer_objects_dir=/cellar/users/snwright/Data/alphafold/test1 \
--job_index=$SLURM_ARRAY_TASK_ID
