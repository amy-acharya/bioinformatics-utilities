# -*- coding: utf-8 -*-
"""
app.py
------
Once the database is built using gdc_data_collector.py
this program can be run for data analysis/visualization.

The program has a web interface using the Streamlit framework.
Three main sections/containers of this program are:
  - dataset (to briefly show the database tables)
  - selections (Input selection via sliders, dropdown menus etc.)
  - results (Output of the program and charts)

 Example:
 --------
   $ streamlit run app.py

"""
__author__ = "Amrita Acharya"
__date__ = "2023/02/16"
__version__ = "1.0.0"

import streamlit as st
import pandas as pd
import sqlite3
import sqlalchemy

header = st.container()
dataset = st.container()
selections = st.container()
results = st.container()

with header:
  st.title("GDC Data Analysis for BRCA")
  st.text("""
    This streamlit app is for data analysis and visualization of GDC data 
    for BRCA collected via another program gdc_data_collector.py
  """)

with dataset:
  st.header("Database Tables")
  st.markdown("The data collected from GDC site is stored in a sqlite3 database in the following tables:")
  st.markdown(":blue[methylation]: Methylation data for CPG islands for each patient")
  st.markdown(":blue[clinical_data]: Demographic data for each patient/case submitter id")
  st.markdown(":blue[idmap]: Mapping table correlating case/submitter id and file id/name")
  st.markdown(":blue[patientid]: Mapping table for File Name to Patient ID")
  st.text("""
        NOTE: Sample dataframe headers for each of the tables below except
        for the methylation table, which is is very big and data retrieval
        takes time...
  """)
  db_name = "gdc.db"
  engine = sqlalchemy.create_engine("sqlite:///%s" % db_name, execution_options={"sqlite_raw_colnames": True})

  for table_name in ["clinical_data", "idmap", "patientid"]:
    subheader_str = 'Table ' + table_name
    st.subheader(subheader_str)
    df = pd.read_sql_table(table_name, engine)
    #https://stackoverflow.com/questions/48171611/difference-between-pandas-read-sql-query-and-read-sql-table
    st.write(df.head(3))


with selections:
  st.header("Data Selection")
  st.text("""
      Age, vital status and other demographic information are used to run 
      a query and find out all patients that have methylation data exceeding
      certain value (e.g. > 0.99). The total count of all such CPG locations
      are determined for each of the patients and displayed in chart under
      the Results section.
  """)
  sel_col, disp_col = st.columns(2)

  CPG = sel_col.slider("CPG Value %age", min_value=850, max_value=1000, value=992)
  CPG = CPG/1000
  AGE = disp_col.slider("Age", min_value=20, max_value=100, value=40)

  GENDER =sel_col.selectbox('Gender', options=['Female', 'Male'], index=0)
  VITAL_STATUS = disp_col.selectbox('Alive/Dead', options=['Alive', 'Dead'], index=0)

  RACE =sel_col.selectbox('Race', options=['White', 'Asian', 'African American'], index=0)
  STAGE = disp_col.selectbox('Pathologic Stage', options=['I', 'II', 'III', 'IA', 'IIA', 'IIIA', 'IIB', 'IIIB', 'IIIC', 'IV', 'X'], index=0)

  RAD_TH =sel_col.selectbox('Radiation Therapy', options=['Yes', 'No'], index=0)
  PH_TH = disp_col.selectbox('Pharmaceutical Therapy', options=['Yes', 'No'], index=0)


with results:
  submitted = st.button("Submit")
  st.header("Results/Charts")
  st.text("""
      The total count of CPG locations exceeding certain value 
      for each of the patients are displayed below.
  """)
  df_results = pd.DataFrame(columns=['Patient_ID', 'Case_ID', 'CPG_Count'])
  if submitted:
    #https://docs.streamlit.io/library/api-reference/status/st.spinner
    with st.spinner('Please wait while data is being processed...'):
      conn = sqlite3.connect('gdc.db')
      cursor = conn.cursor()
      sql = "SELECT File_Name FROM idmap WHERE Case_ID IN (SELECT case_submitter_id FROM clinical_data WHERE age_at_index < " \
            + str(AGE) + " AND vital_status = '" + VITAL_STATUS + "');"

      cursor.execute(sql)
      rows = cursor.fetchall()

      for row in rows:
        file_name = row[0]

        sql = "SELECT Case_ID FROM idmap WHERE File_Name = '" + file_name + "'"
        cursor.execute(sql)
        case_id = cursor.fetchall()[0][0]

        sql = "SELECT Patient_ID FROM patientid WHERE File_Name = '" + file_name + "'"
        cursor.execute(sql)
        data = cursor.fetchall()
      
        if len(data):
          patient_id = data[0][0]
          sql = "SELECT COUNT(*) FROM (SELECT CPG_ISLANDS, " + patient_id + " count_alias FROM methylation WHERE " + patient_id + " > " + str(CPG) + ") src_alias"
          cursor.execute(sql)
          cpg_count = cursor.fetchone()[0]
          if cpg_count:
            df_results.loc[len(df_results.index)] = [patient_id, case_id, cpg_count]

      conn.close()
      st.write(df_results)

    df_results.set_index('Patient_ID', inplace=True)
    chart_data = df_results.drop('Case_ID', axis=1)
    st.bar_chart(data=chart_data)

