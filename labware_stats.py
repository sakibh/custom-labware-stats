import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_echarts import st_echarts
import os
from Google import Create_Service

CLIENT_SECRET_FILE = 'credentials.json'
API_NAME = 'sheets'
API_VERSION = 'v4'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

spreadsheet_id = '***REMOVED***'

result = service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    majorDimension='ROWS',
    range='A1:R'
    ).execute()

# DataFrame
columns = result['values'][0]
data = result['values'][1:]
df = pd.DataFrame(data, columns=columns)

# Total Labware Requests
total_labware_requests = len(df)

# Change Date Format
df['Submitted At'] = pd.to_datetime(df['Submitted At'])

# Bi-Weekly Data
biweekly = df.resample('2W', on='Submitted At').count()
biweekly['Labware Requests'] = biweekly['Name']
biweekly_data = biweekly['Labware Requests']

# Labware Type Count
labware_type_df = pd.DataFrame(df['Type'].value_counts().to_frame())
labware_type_df = labware_type_df.reset_index()
labware_type_df.columns = ['Type', 'Count']

# Labware Status
labware_status_df = pd.DataFrame(df['Status'].value_counts().to_frame())
labware_status_df = labware_status_df.reset_index()
labware_status_df.columns = ['Status', 'Status Count']

# Manufacturer Count
labware_manufacturer_df = pd.DataFrame(df['Manufacturer'].value_counts().to_frame())
labware_manufacturer_df = labware_manufacturer_df.reset_index()
labware_manufacturer_df.columns = ['Manufacturer', 'Count']

#### Dashboard ####
st.set_page_config(layout="wide")
st.title('Custom Labware Statistics')

st.header(f'Total Labware Requests: {total_labware_requests}')
c1, c2 = st.beta_columns((2, 1))
c1.bar_chart(biweekly_data)
c2.write(biweekly_data)

st.header('Labware Types')
c1, c2 = st.beta_columns((2, 1))
fig = px.pie(labware_type_df, values='Count', names='Type', hole=.3)
fig.update_layout(width=1600,height=900)
c1.plotly_chart(fig)
c2.write(labware_type_df)

c1, c2 = st.beta_columns((1, 1))
c1.header('Labware Status')
fig = px.pie(labware_status_df, values='Status Count', names='Status', hole=.3)
c1.plotly_chart(fig)
c2.header('Labware Manufacturer')
fig = px.pie(labware_manufacturer_df, values='Count', names='Manufacturer', hole=.3)
c2.plotly_chart(fig)