import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from skyfield.api import load, wgs84, EarthSatellite
from datetime import datetime, timedelta
import math

# --- CONFIGURATION & CYBERPUNK THEME ---
st.set_page_config(layout="wide", page_title="OrbitGuard | Command", page_icon="🔭")

st.markdown("""
<style>
    /* FORCE DARK MODE & TERMINAL FONT */
    .stApp { background-color: #000508; color: #00ff41; }
    
    /* CUSTOM METRIC BOXES */
    div.stMetric {
        background-color: #0b0f19;
        border: 1px solid #1f2937;
        padding: 15px;
        border-radius: 4px;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.1);
    }
    label { color: #00ff41 !important; font-family: 'Courier New'; }
    .stSlider > div > div > div > div { background-color: #00ff41; }
    h1, h2, h3 { color: #e5e7eb; font-family: 'Courier New', monospace; letter-spacing: -1px; }
    
    /* RADAR GLOW */
    .js-plotly-plot { filter: drop-shadow(0px 0px 5px rgba(0,255,65,0.3)); }
</style>
""", unsafe_allow_html=True)

# --- BACKEND: PHYSICS ENGINE ---
@st.cache_resource
def load_satellites():
    # Cache the data so sliding the time bar is instant
    ts = load.timescale()
    url = 'https://celestrak.org/NORAD/elements/stations.txt'
    try:
        sats = load.tle_file(url)
        return {s.name: s for s in sats}, "LIVE FEED"
    except:
        # Failover TLE (ISS)
        line1 = "1 25544U 98067A   24143.42848900  .00014603  00000+0  26343-3 0  9997"
        line2 = "2 25544  51.6398 108.6657 0004149 105.1328 344.2093 15.50346123455086"
        iss = EarthSatellite(line1, line2, 'ISS (ZARYA)', ts)
        return {'ISS (ZARYA)': iss}, "BACKUP FEED"

# --- SIDEBAR: MISSION CONTROLS ---
st.sidebar.header("🕹️ MISSION CONTROLS")

# 1. Satellite Selector
sat_data, status = load_satellites()
target_name = st.sidebar.selectbox("SELECT TARGET", ["ISS (ZARYA)", "TIANGONG", "HST", "CSS (TIANHE)"])
sat = sat_data.get(target_name, sat_data['ISS (ZARYA)'])

# 2. Time Dilation (The Interactive Predictor)
st.sidebar.markdown("---")
st.sidebar.subheader("⏳ TEMPORAL SHIFT")
time_offset = st.sidebar.slider("Propagate Orbit (Hours)", 0, 24, 0, 1)

# --- MAIN PHYSICS CALCULATIONS ---
ts = load.timescale()
t_now = ts.now()
# Apply the "Time Dilation" from the slider
t_future = ts.from_datetime(datetime.utcnow() + timedelta(hours=time_offset))

# Calculate Position at t_future
geocentric = sat.at(t_future)
subpoint = wgs84.subpoint(geocentric)
speed = np.linalg.norm(geocentric.velocity.km_per_s)

# --- UI LAYOUT ---

# Header with "Hacker" status
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title(f"// {target_name} COMMAND")
    if time_offset > 0:
        st.caption(f"⚠️ SIMULATING FUTURE TRAJECTORY: T+{time_offset} HOURS")
    else:
        st.caption("🔴 LIVE TELEMETRY STREAM")
with col_h2:
    st.metric("SYS.STATUS", status)


# ROW 1: THE VISUALS (Radar & Globe)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📡 LOCAL RADAR (RICHMOND)")
    # Calculate Sky Plot (Azimuth/Elevation relative to Richmond)
    # This is "Look Angle" Math
    richmond = wgs84.latlon(49.1666, -123.1336)
    difference = sat - richmond
    topocentric = difference.at(t_future)
    alt, az, distance = topocentric.altaz()
    
    # Polar Plot
    fig_radar = go.Figure(go.Scatterpolar(
        r=[90 - alt.degrees if alt.degrees > 0 else None], # Radius (90 is center)
        theta=[az.degrees if alt.degrees > 0 else None],   # Angle
        mode='markers',
        marker=dict(color='#00ff41', size=20, symbol='cross-thin-open'),
        name=target_name
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 90], showticklabels=False), # 90 degrees (horizon) to 0 (zenith)
            angularaxis=dict(direction="clockwise", rotation=90, color="#00ff41"),
            bgcolor="#0b0f19"
        ),
        paper_bgcolor="#00000000",
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    
    if alt.degrees > 0:
        st.success(f"✅ TARGET VISIBLE: {alt.degrees:.1f}° ELEVATION")
    else:
        st.error("❌ TARGET BELOW HORIZON")

with col2:
    st.subheader("🌍 ORBITAL PROJECTION")
    
    # Calculate Path (Past and Future)
    mins = np.arange(-90, 90, 2) # 3 hours of path
    times_path = ts.utc(t_future.utc_datetime().year, t_future.utc_datetime().month, t_future.utc_datetime().day, 
                        t_future.utc_datetime().hour, t_future.utc_datetime().minute + mins)
    path_geo = sat.at(times_path)
    path_sub = wgs84.subpoint(path_geo)
    
    fig_globe = go.Figure()
    
    # The Path
    fig_globe.add_trace(go.Scattergeo(
        lon=path_sub.longitude.degrees, lat=path_sub.latitude.degrees,
        mode='lines', line=dict(width=2, color='#00441b'), # Dark Green ghost path
        name='Trajectory'
    ))
    
    # The Satellite (At Selected Time)
    fig_globe.add_trace(go.Scattergeo(
        lon=[subpoint.longitude.degrees], lat=[subpoint.latitude.degrees],
        mode='markers', marker=dict(size=15, color='#00ff41', symbol='diamond'), # Bright Green
        name='Target'
    ))

    fig_globe.update_geos(
        projection_type="orthographic",
        showland=True, landcolor="#0f172a",
        showocean=True, oceancolor="#020617",
        showcountries=False, showlakes=False
    )
    fig_globe.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor="#00000000",
        height=400
    )
    st.plotly_chart(fig_globe, use_container_width=True)

# ROW 2: THE APPLICABLE PHYSICS (Vis-Viva Calculator)
st.markdown("---")
st.subheader("🚀 MANEUVER CALCULATOR (VIS-VIVA SOLVER)")

c1, c2, c3 = st.columns(3)

with c1:
    st.info("CURRENT ORBIT")
    r_current = 6378 + subpoint.elevation.km # Radius from Earth Center
    st.metric("Semi-Major Axis (r1)", f"{r_current:.1f} km")

with c2:
    st.warning("TARGET ORBIT")
    target_alt = st.number_input("Desired Altitude (km)", value=500, min_value=300, max_value=2000)
    r_target = 6378 + target_alt

with c3:
    st.success("REQUIRED DELTA-V")
    # THE PHYSICS: Hohmann Transfer Delta-V Calculation
    mu = 398600 # Earth Gravitational Parameter
    
    # Velocity at Perigee (Burn Point)
    v1 = math.sqrt(mu / r_current)
    # Velocity required for Transfer Ellipse
    v_transfer = math.sqrt(mu * (2/r_current - 2/(r_current + r_target)))
    
    delta_v = abs(v_transfer - v1) * 1000 # Convert to m/s
    
    st.metric("Δv (Burn)", f"{delta_v:.2f} m/s", delta="Fuel Cost")

st.caption("Calculation based on Hohmann Transfer optimality. Assumes coplanar circularization.")
