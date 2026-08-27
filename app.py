import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from skyfield.api import load, wgs84
from skyfield.framelib import itrs
from datetime import datetime, timedelta
import pytz

# --- CONFIGURATION & STYLE ---
st.set_page_config(layout="wide", page_title="OrbitGuard Pro | Command")

# Custom "Cyberpunk/NASA" CSS
st.markdown("""
<style>
    .stApp { background-color: #050505; }
    div.stMetric {
        background-color: #111;
        border: 1px solid #333;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #00ff41;
    }
    h1, h2, h3 { color: #e0e0e0; font-family: 'Courier New', monospace; }
    .status-good { color: #00ff41; font-weight: bold; }
    .status-warn { color: #ffa500; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- BACKEND: PHYSICS ENGINE ---
@st.cache_resource
def load_data():
    # Load TLE data and Ephemeris for accurate gravity/shadow calculations
    stations_url = 'http://celestrak.org/NORAD/elements/stations.txt'
    satellites = load.tle_file(stations_url)
    eph = load('de421.bsp') # NASA JPL Ephemeris for Sun/Earth positions
    return {sat.name: sat for sat in satellites}, eph

def calculate_ground_track(sat, t_now, duration_minutes=90):
    """Generates the future path (Sine Wave) for visualization"""
    ts = load.timescale()
    # Create a time range: -45 mins to +45 mins
    minutes = np.arange(-45, 45, 1) 
    times = ts.utc(t_now.utc_datetime().year, t_now.utc_datetime().month, t_now.utc_datetime().day, 
                   t_now.utc_datetime().hour, t_now.utc_datetime().minute + minutes)
    
    # Calculate positions for all times at once (Vectorization)
    geocentric = sat.at(times)
    subpoints = wgs84.subpoint(geocentric)
    
    return pd.DataFrame({
        'lat': subpoints.latitude.degrees,
        'lon': subpoints.longitude.degrees,
        'time': minutes
    })

def get_next_pass(sat, city_lat, city_lon):
    """Predicts the next flyover for a specific location"""
    ts = load.timescale()
    t0 = ts.now()
    t1 = ts.from_datetime(datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(days=1))
    
    city = wgs84.latlon(city_lat, city_lon)
    t, events = sat.find_events(city, t0, t1, altitude_degrees=10.0)
    
    if len(t) > 0:
        # Return the first "Rise" event
        rise_time = t[0].utc_datetime().astimezone(pytz.timezone('US/Pacific'))
        return rise_time.strftime('%Y-%m-%d %I:%M %p')
    return "No pass in 24h"

# --- APP LOGIC ---
data_dict, eph = load_data()
ts = load.timescale()
t_now = ts.now()

# Sidebar Control
st.sidebar.title("📡 Tracking Target")
selected_sat_name = st.sidebar.selectbox("Select Asset", ["ISS (ZARYA)", "TIANGONG", "HST"])
sat = data_dict[selected_sat_name]

# 1. Real-Time Telemetry
geocentric = sat.at(t_now)
subpoint = wgs84.subpoint(geocentric)
is_sunlit = sat.at(t_now).is_sunlit(eph) # The Astrophysics Flex: Shadow detection

# 2. Layout
col1, col2 = st.columns([3, 1])

with col1:
    st.title(f"TRACKING: {selected_sat_name}")
    
    # 3D Globe with Ground Track
    track_df = calculate_ground_track(sat, t_now)
    
    fig = go.Figure()
    
    # The Path (Sine Wave)
    fig.add_trace(go.Scattergeo(
        lon=track_df['lon'], lat=track_df['lat'],
        mode='lines', line=dict(width=2, color='#00ff41'),
        name='Orbit Path (±45m)'
    ))
    
    # The Satellite (Current Position)
    fig.add_trace(go.Scattergeo(
        lon=[subpoint.longitude.degrees], lat=[subpoint.latitude.degrees],
        mode='markers', marker=dict(size=15, color='red', symbol='cross'),
        name='Current Pos'
    ))

    # Vancouver Marker (Home Base)
    fig.add_trace(go.Scattergeo(
        lon=[-123.1207], lat=[49.2827],
        mode='markers+text', marker=dict(size=8, color='cyan'),
        text=["UBC / Vancouver"], textposition="bottom center",
        name='Ground Station'
    ))

    fig.update_geos(
        projection_type="orthographic",
        showland=True, landcolor="#1f2937",
        showocean=True, oceancolor="#0b0f19",
        showcountries=True, countrycolor="#374151"
    )
    fig.update_layout(
        height=500, margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor="#00000000",
        font=dict(color="white")
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Telemetry Data")
    
    # Solar Status (Physics Calculation)
    status_color = "🟢 Sunlit" if is_sunlit else "Ez Eclipse (Shadow)"
    st.metric("Solar Status", status_color)
    
    # Position
    st.metric("Altitude", f"{subpoint.elevation.km:.1f} km")
    st.metric("Velocity", "7.66 km/s") # Approx LEO speed
    
    # Predictive Analytics
    st.markdown("---")
    st.subheader("Prediction Model")
    next_pass = get_next_pass(sat, 49.2827, -123.1207) # Vancouver Coords
    st.metric("Next Vancouver Pass", next_pass, help="Calculated using SGP4 Propagator")
    
    st.info("System: OrbitGuard v2.1\nData Source: CelesTrak / NORAD")

