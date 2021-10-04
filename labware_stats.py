import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
import os
from Google import Create_Service
import re
import datetime
from datetime import timedelta

CLIENT_SECRET_FILE = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
API_NAME = 'sheets'
API_VERSION = 'v4'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

spreadsheet_id = os.environ.get('SHEETS_ID')

result = service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    majorDimension='ROWS',
    range='A1:R'
    ).execute()

# DataFrame
columns = result['values'][0]
data = result['values'][1:]
df = pd.DataFrame(data, columns=columns)
pd.set_option('display.max_columns', None)

# Change Date Format
df['Submitted At'] = pd.to_datetime(df['Submitted At']).dt.normalize()

# Clean Up Manufacturers Data
df['Manufacturer'][df['Manufacturer'] == 'Manufacturer not listed below'] = df['< text field']


class DataProcessor:
    def __init__(self, data):
        self.data = data

    def get_data(self):
        return self.data

    def filter_by_date(self, start_date, end_date):
        start_date = start_date.strftime('%m/%d/%Y')
        end_date = end_date.strftime('%m/%d/%Y')
        date_filter = (self.data['Submitted At'] > start_date) & (self.data['Submitted At'] <= end_date)
        self.data = self.data.loc[date_filter]
        return len(self.data) 

    def get_biweekly_data(self):
        df = self.data.resample('2W', on='Submitted At').count()
        return df['Name']

    def get_labware_type(self):
        df = pd.DataFrame(self.data['Type'].value_counts().to_frame())
        df = df.reset_index()
        df.columns = ['Type', 'Count']
        labware_tips_count = df[df.Type.str.contains('Tip', flags=re.IGNORECASE, regex=True)].sum()
        df2 = {'Type': 'Tips', 'Count': labware_tips_count['Count']}
        df = df[~df.Type.str.contains('Tip', flags=re.IGNORECASE, regex=True)]
        df = df.append(df2, ignore_index=True)
        return df

    def get_labware_status(self):
        df = pd.DataFrame(self.data['Status'].value_counts().to_frame())
        df = df.reset_index()
        df.columns = ['Status', 'Count']
        return df

    def get_manufacturer_count(self):
        df = pd.DataFrame(self.data['Manufacturer'].value_counts().to_frame())
        df = df.reset_index()
        df.columns = ['Manufacturer', 'Count']
        return df

    def get_wellplate_manufacturers(self):
        df = self.data[self.data['Type'] == 'Well Plate']
        df = pd.DataFrame(df['Manufacturer'].value_counts().to_frame())
        df = df.reset_index()
        df.columns = ['Manufacturer', 'Count']
        return df

    def get_tip_manufacturers(self):
        # tips_re = re.compile('Tips')
        df = self.data[self.data['Type'].str.contains(r'Tip|tip')]
        df = pd.DataFrame(df['Manufacturer'].value_counts().to_frame())
        df = df.reset_index()
        df.columns = ['Manufacturer', 'Count']
        return df

    def get_lc_tool_data(self):
        df = pd.DataFrame(self.data['Have you seen our Labware Creator tool?'].value_counts().to_frame())
        df = df.reset_index()
        df.columns = ['Prompts', 'Count']
        return df


def get_two_week_date():
    today = datetime.date.today()
    two_weeks_ago = today - timedelta(days=365)
    return two_weeks_ago


labwareStats = DataProcessor(df)

# Default Date Range
labwareStats.filter_by_date(get_two_week_date(), datetime.date.today())

#### Dashboard ####
st.set_page_config(layout='wide', page_title='Custom Labware Statistics')
st.title('Custom Labware Statistics')

# Total Labware Requests

# Report Date Range
c1, c2, c3, c4, c5 = st.beta_columns((1, 1, 1, 1, 1))
start = c1.date_input("Start Date", get_two_week_date())
end = c2.date_input("End Date", datetime.date.today())
if st.button('Run'):
    labwareStats.filter_by_date(start, end)

# Bi-Weekly Data Chart
st.header(f'Total Labware Requests: {len(labwareStats.get_data())}')
# st.bar_chart(labwareStats.get_biweekly_data())

# Labware Types/Status
c1, c2 = st.beta_columns((1, 1))
c1.header('Labware Types')
# fig1 = px.pie(labwareStats.get_labware_type(), values='Count', names='Type', hole=.3)
# fig1.update_traces(textposition = 'inside')
# c1.write(labwareStats.get_labware_type())
fig1 = go.Figure(data=[go.Table(
        header=dict(values=list(labwareStats.get_labware_type().columns),
                    fill_color='lightskyblue',
                    align='left'),
        cells=dict(values=[labwareStats.get_labware_type().Type, labwareStats.get_labware_type().Count],
                   fill_color='rgba(0,0,0,0)',
                   font=dict(color='white', size=18),
                   height=40,
                   align='left'))
    ])

c2.header('Labware Status')
fig2 = px.pie(labwareStats.get_labware_status(), values='Count', names='Status', hole=.3)
fig2.update_traces(textposition = 'inside')
fig1.update_layout(width=800, height=640)
c1.plotly_chart(fig1)
c2.plotly_chart(fig2)

# Manufacturers/Well Plate Manufacturer
c1, c2 = st.beta_columns((1, 1))
c1.header('Labware Manufacturers')
fig1 = px.pie(labwareStats.get_manufacturer_count(), values='Count', names='Manufacturer', hole=.3)
fig1.update_traces(textposition = 'inside')
c1.plotly_chart(fig1)
c2.header('Well Plate Manufacturers')
fig2 = px.pie(labwareStats.get_wellplate_manufacturers(), values='Count', names='Manufacturer', hole=.3)
c2.plotly_chart(fig2)

# Tip Manufacturer
c1, c2 = st.beta_columns((1, 1))
c1.header('Tip Manufacturers')
fig1 = px.pie(labwareStats.get_tip_manufacturers(), values='Count', names='Manufacturer', hole=.3)
fig1.update_traces(textposition='inside')
c1.plotly_chart(fig1)
c2.header('Labware Creator Tool')
fig2 = px.pie(labwareStats.get_lc_tool_data(), values='Count', names='Prompts', hole=.3)
fig2.update_traces(textposition='inside')
c2.plotly_chart(fig2)

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)