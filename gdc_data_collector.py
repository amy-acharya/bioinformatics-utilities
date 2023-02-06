# -*- coding: utf-8 -*-
"""
 gdc_data_collector.py
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
 
 Example:
 --------
   $ python3 gdc_data_collector.py

 About the GDC data:
 -------------------
   Each methylation data will have its own folder with a methylation data 
   file and optionally an annotation file. Each TCGA file contains 
   CpG island location data in the first column and methylation data in the 
   second column. All files have identical CpG location data in the same order.
 
 This module does the following tasks:
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
 
 Inputs:
 -------
   None. Just need to run python3 <program name>, no other arguments.
   However, the GDC data folders need to under the same dir as the program.  
 Outputs:
 --------
   The program doesn't return anything to stdout.
   However, it creates two CSV files under the same directory.
    all_data.csv: Methylation data of all patients combined into one CSV file.
    focus_data.csv: Subset of data with methylation > 0.9 for further study.

 TO-DO:
 ----
   Explore downloading data directly from GDC site via API access/other means.
   Other enhancements as needed for an ongoing research.
"""
__author__ = "Amrita Acharya"
__date__ = "2023/01/16"
__version__ = "0.0.1"

import pandas as pd                # pandas library for processing bulk data 
import os                          # for os functionalities
import glob                        # find all pathnames matching pattern
import shutil                      # for file operations in python
from pathlib import Path           # to extract file name from the full path

def main():
  # Recursively search all dirs
  # pick any .txt file that has methylation in filename.
  frames = []
  curr_dir = os.getcwd()
  all_files = glob.glob(curr_dir + '/**/*.txt', recursive=True)
  tcga_files = [file for file in all_files if "methylation" in file]

  # create Empty DataFrame 
  df = pd.DataFrame()

  # Create a data frame for each patient, add the dfs to a list.
  for i in range(len(tcga_files)):

    df = 'df' + str(i)
    tcga_file = tcga_files[i]

    # read_table instead read_csv because of default separator (\t)
    df = pd.read_table(tcga_file, header=None, float_precision=None)

    # Patient ID has string has 2 parts concatenated together:
    #  - Patient0, Patient1... for easy human read...
    #  - 1st 16 char of file name, to keep track where the data came from...
    patientid = 'Patient' + str(i) + ':' + Path(tcga_file).stem[0:16]

    # Add column names
    df.columns = ['Gene-Location', patientid]
    frames.append(df)

  # Take frame[0] as the base and merge the remaining frames.
  # merge because the keys(Gene-Location) are the same.
  df = frames[0]
  for i in range(1, len(frames)):
    curr_df = frames[i]
    df = pd.merge(df, curr_df, on='Gene-Location')

  # Re-index to make Gene-Location the index.
  df.set_index('Gene-Location', inplace=True)
  #df.fillna(value='NA', inplace=True)

  # Write all data to a CSV file
  df_alldata = df.fillna(value='NA')
  print(df_alldata.head(10))
  df_alldata.to_csv('all_data.csv')

  # Write focused data to a CSV file
  f = open("focus_data.csv", mode="w")
  for col in df.columns:
    genelocs = df[df[col] >0.9 ].index.values
    for gl in genelocs:
      f.write(f'{gl},{col},{df.loc[gl][col]}\n')
  f.close()

if __name__ == "__main__":
    main()



