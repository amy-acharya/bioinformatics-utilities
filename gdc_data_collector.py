# -*- coding: utf-8 -*-
"""
 gdc_data_collector.py
 ----------------------
   This program is for gathering data from the NIH National Cancer Institute 
   GDC Data Portal - https://portal.gdc.cancer.gov/.

   The program doesn't download the data itself. Data needs to be downloaded
   from the GDC site and unzipped/untarred and placed in the same directory
   as the program gdc_data_collector.py. A better way to collect the data
   folders/files is to use the gdc-client bulk transfer tool. 

   The program processes the collected methylation data and stores them in
   various tables in a sqlite3 database. After that, a streamlit app, app.py,
   can be run for data processing/analysis and visualization.

 Example:
 --------
   $ python3 gdc_data_collector.py

 About the GDC data:
 -------------------
   Each sample from a patient will have its own folder with a methylation data
   file and optionally an annotation file. Each TCGA file contains CpG island
   location data in the first column and methylation beta value in the second
   column. All files have identical gene location data in the same order.

 This module does the following tasks:
 -------------------------------------
   * Recursively search all folders for TCGA files and save in a list.
   * Create a pandas dataframe for each file.
   * Name the gene location column header.
   * Construct the methylation data headers by taking the filename, 
      concatenating an ID for the patient, and replacing hyphens ('-') with
      underscores ('_') to conform to SQLite syntax.
      The filename helps track back to the original file ID.
   * Save the dataframe names in a list. Iterate the list and merge them
       into one big dataframe (merge on the 'CPG_ISLANDS' column since it's 
       the same for all frames).
   * Write the dataframe to a table named 'methylation'. This is the biggest
       table in the database (over 485K rows and close to 900 columns)
   * Other database tables are smaller and used for various correlations:
       - clinical_data (Demographic data for each patient/case submitter id)
       - idmap (Mapping table correlating case/submitter id and file id/name)
       - patientid (Mapping table for file name to patient ID)

 Inputs:
 -------
   None. Just need to run python3 <program name>, no other arguments.
   However, the GDC data folders need to under the same folder as the program.

 Outputs:
 --------
   The program doesn't return anything to stdout. However, it creates the 
   SQLite3 database (gdc.db) along with all the tables mentioned above.

 TODO:
 ----
   - Explore making the data download task part of the program itself.
   - Currently, the database tables are simple and not properly normalized.
     Can be normalized/optimized to avoid multiple queries.
   - Other enhancements as needed for ongoing research.
"""
__author__ = "Amrita Acharya"
__date__ = "2023/01/16"
__version__ = "1.0.0"


import pandas as pd                # pandas library for processing bulk data 
import os                          # for os functionalities
import glob                        # find all pathnames matching pattern
import shutil                      # for file operations in python
from pathlib import Path           # to extract file name from the full path
import sqlite3
#import sqlalchemy
import argparse
import time

def create_methylation_db():

  conn = sqlite3.connect('gdc.db')
  cursor = conn.cursor()
  cursor.execute("DROP TABLE IF EXISTS methylation")
  cursor.execute("DROP TABLE IF EXISTS patientid")

  # Recursively search all dirs
  # pick any .txt file that has methylation in filename.
  frames = []
  curr_dir = os.getcwd()
  all_files = glob.glob(curr_dir + '/**/*.txt', recursive=True)
  tcga_files = [file for file in all_files if "methylation" in file]

  # create Empty DataFrame
  df = pd.DataFrame()

  # Create a data frame for each patient, add the df's to a list.

  df_patid = pd.DataFrame(columns=['File_Name', 'Patient_ID'])
  for i in range(len(tcga_files)):

    df = 'df' + str(i)
    tcga_file = tcga_files[i]

    # read_table instead read_csv because of default separator (\t)
    df = pd.read_table(tcga_file, header=None, float_precision=None)

    # Patient ID has string has 2 parts concatenated together:
    #  - Patient0, Patient1... for easy human read...
    #    Also, to avoid sqlite syntax errors (cannot start with a number)
    #  - UUID portion (methylation file name) for unique identification.
    # Hyphens are replaced with underscore (again to avoid syntax error)
    file_name = Path(tcga_file).stem.split('.')[0]
    patient_id =  'Patient' + str(i) + '-' + file_name
    patient_id = patient_id.replace('-', '_')
    df_patid.loc[len(df_patid.index)] = [file_name, patient_id]

    # Add column names
    df.columns = ['CPG_ISLANDS', patient_id]
    frames.append(df)

  # Create the sql table from the pandas dataframe.
  df_patid.to_sql('patientid', conn, if_exists = 'replace', index=False)

  # Take frame[0] as the base and merge the remaining frames.
  # merge because the keys(CPG_ISLANDS) are the same.
  df = frames[0]
  df0 = df.iloc[:, 0]

  for i in range(len(frames)):
    curr_df = frames[i]
    df = pd.merge(df, curr_df, on='CPG_ISLANDS')
    print('  ...Frames Merged: ', i)

  column_headers = list(df.columns.values)
  methylation_cols = column_headers[1:]

  # Create the sql table from the pandas dataframe.
  df.to_sql('methylation', conn, if_exists = 'replace', index=False)
  conn.commit()
  conn.close()

def create_mapping_db():
  conn = sqlite3.connect('gdc.db')
  cursor = conn.cursor()
  cursor.execute("DROP TABLE IF EXISTS idmap")

  # Mapping Table: File ID/File Name <-> Case ID
  # The file gdc_sample_sheet.2023-02-16.csv was downloaded from GDC site.
  df_mapping = pd.read_csv('gdc_sample_sheet.2023-02-16.csv')
  columns = df_mapping.columns
  columns = [i.replace(' ', '_') for i in columns]
  df_mapping.columns = columns
  df_mapping = df_mapping[['Case_ID', 'File_ID', 'File_Name']]
  df_mapping['File_Name'] = df_mapping['File_Name'].map(lambda x: x.rstrip('.methylation_array.sesame.level3betas.txt'))
  df_mapping.to_sql('idmap', conn, if_exists = 'replace', index=False)

  conn.commit()
  conn.close()

def create_clinical_db():
  conn = sqlite3.connect('gdc.db')
  cursor = conn.cursor()
  cursor.execute("DROP TABLE IF EXISTS clinical_data")
  # Clinical Data Table based on file clinical_data.csv downloaded from GDC site.
  df_clinical = pd.read_csv('clinical_data.csv')
  df_clinical.to_sql('clinical_data', conn, if_exists = 'replace', index=False)
  conn.commit()
  conn.close()

def main():
  # NOTE: Initial idea was the same program gdc_data_collector.py to do the data
  # collection and analysis. Hence I had the argparse to pass command line options.
  # But later, I moved the data analysis/visualization to a streamlit app. 
  # Hence argparse is really not needed in this program anymore...
  parser = argparse.ArgumentParser(description ='GDC Data Analyzer Command Line Options...')
  parser.add_argument("-b", "--build", action="store_true", help="Build Database Tables")
  
  args = parser.parse_args()
  if args.build:
    print("Building Database tabless")
    create_methylation_db()
    create_mapping_db()
    create_clinical_db()
    print("Database created")
  else:
    print("Database built already, execute 'streamlit run app.py' to process/analyze.")

if __name__ == "__main__":
    main()



