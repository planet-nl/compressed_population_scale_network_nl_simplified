# Author: Eszter Bokanyi, e.bokanyi@liacs.leidenuniv.nl, 2025.11.18.

# This script takes the series of longitudinal raw networks and creates 5-layer undirected networks based on the group
# column in the layer file of the raw networks.

# It excludes institutional household, ties by-partnership kin ties, and random buurt neighbor link ties.

input_folder="H:\\ODISSEI_portal_A"
output_folder="H:\\ODISSEI_portal_B"
start_year=2009
end_year=2023

log_file="$output_folder/log_messages_$(date +'%Y-%m-%d_%H-%M-%S').log"
error_file="$output_folder/log_error_$(date +'%Y-%m-%d_%H-%M-%S').log"
echo -e "RUN $(date +'%Y-%m-%d_%H-%M-%S')\n\n" >$log_file
echo -e "RUN $(date +'%Y-%m-%d_%H-%M-%S')\n\n" >$error_file

for year in `seq $start_year $end_year`
do
    echo -e "==============================\n YEAR $year \n==============================" | tee -a $log_file $error_file
    /c/mambaforge/envs/9629/python.exe "$(dirname "$0")/grouped_networks.py" $input_folder $output_folder $year >>$log_file 2>>$error_file
done
    