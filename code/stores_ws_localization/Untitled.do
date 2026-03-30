/*
Version : 1
Author: Sophia Aristizabal
Objective: Clean the raw data of crime just for Bogota
*/

global global_dir "/Users/sophiaaristizabal/Desktop/1 economia/thesis_economics"

global dir_data "$global_dir/data/crime" // this is where all the EODH is located

global dir_raw "$global_dir/data/crime/raw_data_crimen" // this is where all the EODH is located

global dir_processed "$global_dir/data/crime/bogota_crime" // this is where all the EODH is located

cd "$dir_data"


clear all

//open sexual crime Excel

//drop unessential variables
import excel "", firstrow clear



//add variable with all ones (for the type of crime)




//after cleaning, append all dataset into a single one (convert it into csv)
