import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import requests, os
from gwpy.timeseries import TimeSeries
from gwosc.locate import get_urls
from gwosc import datasets
from gwosc.api import fetch_event_json

from copy import deepcopy
import base64

from helper import make_audio_file

# Use the non-interactive Agg backend, which is recommended as a
# thread-safe backend.
# See https://matplotlib.org/3.3.2/faq/howto_faq.html#working-with-threads.
import matplotlib as mpl
mpl.use("agg")

##############################################################################
# Workaround for the limited multi-threading support in matplotlib.
# Per the docs, we will avoid using `matplotlib.pyplot` for figures:
# https://matplotlib.org/3.3.2/faq/howto_faq.html#how-to-use-matplotlib-in-a-web-application-server.
# Moreover, we will guard all operations on the figure instances by the
# class-level lock in the Agg backend.
##############################################################################
from matplotlib.backends.backend_agg import RendererAgg
_lock = RendererAgg.lock





# -- Set page config
apptitle = 'GW Quickview'

st.set_page_config(page_title=apptitle, page_icon=":eyeglasses:")

# -- Default detector list
detectorlist = ['H1','L1', 'V1']

# Title the app
st.title('Time Series Data')

st.markdown("""
 * Use the menu at left to select data and set plot parameters
 * Your plots will appear below
""")

@st.cache(ttl=3600, max_entries=10)   #-- Magic command to cache data
def load_gw(t0, detector, fs=4096):
    strain = TimeSeries.fetch_open_data(detector, t0-14, t0+14, sample_rate = fs, cache=False)
    return strain

@st.cache(ttl=3600, max_entries=10)   #-- Magic command to cache data
def get_eventlist():
    allevents = datasets.find_datasets(type='events')
    eventset = set()
    for ev in allevents:
        name = fetch_event_json(ev)['events'][ev]['commonName']
        if name[0:2] == 'GW':
            eventset.add(name)
    eventlist = list(eventset)
    eventlist.sort()
    return eventlist
    
st.sidebar.markdown("## Select Data Time and Detector")

# -- Get list of events
eventlist = get_eventlist()

#-- Set time by GPS or event
select_event = st.sidebar.selectbox('How do you want to find data?',
                                    ['By Date','By Category', 'By Satellite', 'By Source'])

select_event_two = st.sidebar.selectbox('Select Location',
                                    ['By coordinates'])

if select_event == 'By Category':
    # -- Set a GPS time:        
    str_t0 = st.sidebar.selectbox('Category',['noaa-goes16/ABI-L1b-RadC', 'noaa-goes16/ABI-L1b-RadF', 'noaa-goes16/ABI-L1b-RadM','noaa-goes16/ABI-L2-ACHAC', 'noaa-goes16/ABI-L2-ACHAF',
'noaa-goes16/ABI-L2-ACHAM',
'noaa-goes16/ABI-L2-ACHTF',
'noaa-goes16/ABI-L2-ACHTM',
'noaa-goes16/ABI-L2-ACMC',
'noaa-goes16/ABI-L2-ACMF',
'noaa-goes16/ABI-L2-ACMM',
'noaa-goes16/ABI-L2-ACTPC',
'noaa-goes16/ABI-L2-ACTPF',
'noaa-goes16/ABI-L2-ACTPM',])    # -- GW150914
    

else:
    chosen_event = st.sidebar.selectbox('By Satellite', eventlist)
    t0 = datasets.event_gps(chosen_event)
    detectorlist = list(datasets.event_detectors(chosen_event))
    detectorlist.sort()
    st.subheader(chosen_event)
    st.write('GPS:', t0)
    
    
    # -- Experiment to display masses
    try:
        jsoninfo = fetch_event_json(chosen_event)
        for name, nameinfo in jsoninfo['events'].items():        
            st.write('Mass 1:', nameinfo['mass_1_source'], 'M$_{\odot}$')
            st.write('Mass 2:', nameinfo['mass_2_source'], 'M$_{\odot}$')
            st.write('Network SNR:', int(nameinfo['network_matched_filter_snr']))
            eventurl = 'https://gw-osc.org/eventapi/html/event/{}'.format(chosen_event)
            st.markdown('Event page: {}'.format(eventurl))
            st.write('\n')
      
    except:
        pass

    
#-- Choose detector as H1, L1, or V1
detector = st.sidebar.selectbox('Detector', detectorlist)

# -- Select for high sample rate data
fs = 4096
maxband = 2000
high_fs = st.sidebar.checkbox('Full sample rate data')
if high_fs:
    fs = 16384
    maxband = 8000





