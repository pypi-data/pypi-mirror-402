#!/bin/bash
#SBATCH --job-name=af_msa
#SBATCH --output=/cellar/users/snwright/Data/SlurmOut/af_%A_%a.out
#SBATCH --error=/cellar/users/snwright/Data/SlurmOut/af_%A_%a.err
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --partition=nrnb-compute
#SBATCH --account=nrnb
#SBATCH --array=1-21%10
#SBATCH --time=2-00:00:00

inputdir=/cellar/users/snwright/Git/AlphaPulldown/example_data
afdir=/cellar/users/snwright/Git/AlphaPulldown/alphapulldown

python -u $afdir/create_individual_features.py \
  --fasta_paths=$inputdir/baits.fasta,$inputdir/example_1_sequences_shorter.fasta \
  --data_dir=/cellar/shared/alphafold/ \
  --save_msa_files=False \
  --output_dir=/cellar/users/snwright/Data/alphafold/test1/ \
  --use_precomputed_msas=False \
  --max_template_date=2050-01-01 \
  --skip_existing=False \
  --use_mmseqs2=True \
  --seq_index=$SLURM_ARRAY_TASK_ID
