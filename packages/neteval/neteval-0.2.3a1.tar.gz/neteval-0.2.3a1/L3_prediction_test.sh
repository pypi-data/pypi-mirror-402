#!/bin/sh
#SBATCH --job-name=l3_test
#SBATCH --output=/cellar/users/snwright/Data/SlurmOut/l3_test_%A.out
#SBATCH --error=/cellar/users/snwright/Data/SlurmOut/l3_test_%A.err    # Standard output and error log
#SBATCH --cpus-per-task=1    # Number of CPUs per task
#SBATCH --mem-per-cpu=15G    # Memory per CPU
#SBATCH --time=1-00:00:00    # Maximum execution time
name=bind.v8
execdir="/cellar/users/snwright/Data/Network_Analysis/Edge_Prediction/kpisti-L3-ed6b18f/"
file="/cellar/users/snwright/Data/Network_Analysis/Processed_Data/v2_final/bind.v8_net.txt"
outpath="/cellar/users/snwright/Data/Network_Analysis/Edge_Prediction/L3_outputs/"


cd $execdir

# check the number of columns
num_col=$(awk -F'\t' '{print NF; exit}' $file)
# if no score column, add a score column
# if number of columns == 3
if [[ "$num_col" -eq 3 ]]; then
    awk -F"\t" '(NR>1){print $1 "\t" $2 "\t" 1.0}' $file > ./${name}_temp_input_file.txt
else
    awk -F"\t" '(NR>1){print $1 "\t" $2 "\t" $3}' $file > ./${name}_temp_input_file.txt
# move to the directory. 
fi

./L3.out ${name}_temp_input_file.txt

mv ${name}_temp_input_file.txt $file

mv L3_predictions_${name}_temp_input_file.txt.dat $outpath/L3_predictions_${name}.dat

