
# Bioinformatics Utilities
## TCGA Methylation Data
 #### gdc_data_collector.py
 ----------------------
   Data gathering from NIH National Cancer Institute GDC Data Portal.
   This program processes methylation data collected from the above portal.
   The program doesn't download the data itself. Data needs to be downloaded
   from the GDC site and unzipped/untarred and placed in the same directory
   as the program gdc_data_collector.py. Two CSV files are created as outputs
   of this program: all_data.csv (methylation data for all patients combined
   into one CSV file for further analysis) and focus_data.csv (subset of data
   meeting some criteria along with gene location and patient id for further/
   focused study).

   Data collected from https://portal.gdc.cancer.gov/.
 
#### Example:
 --------

       $ python3 gdc_data_collector.py

 #### About the GDC data:
 -------------------
   Each methylation data will have its own folder with a methylation data 
   file and optionally an annotation file. Each TCGA file contains 
   CpG island location data in the first column and methylation data in the 
   second column. All files have identical CpG location data in the same order.
 
 #### This module does the following tasks:
 -------------------------------------
   * Recursively search all dir for TGCA files and save in a list.
   * Create a pandas dataframe for each file.
   * Name the gene location column header Gene-Location.
   * Construct the methylation data headers by taking 16 chars from
      the filename and also concatenating an id for the patient.
      filename part will help us track back to the original file if needed.
   * Save the dataframe names in a list.
   * Iterate the list of dataframes and merge them into one big dataframe
       merge on='Gene-Location' column since it's the same for all frames.
   * Make the 'Gene-Location' column the index of the dataframe.
   * Fill all the missing data (NaN) as 'NA' for better readability
   * Write the dataframe to a CSV file (all_data.csv).
   * Iterate the data in the dataframe, for any value > 0.9
       gather the row/index (gene location), column (patient id), and value
       write to another csv file to focus on this data for further study.
 #### Inputs:
 -------
 None. Just need to run python3 `program name`, no other arguments.
 However, the GDC data folders need to under the same dir as the program.  
 Outputs:

The program doesn't return anything to stdout.
However, it creates two CSV files under the same directory.
`all_data.csv`: Methylation data of all patients combined into one CSV file.
`focus_data.csv`: Subset of data with methylation > 0.9 for further study.

 #### TO-DO:
 ----
   Explore downloading data directly from GDC site via API access/other means.
   Other enhancements as needed for an ongoing research.
