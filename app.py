import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from skyfield.api import load, wgs84, EarthSatellite
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURATION & CAS THEME ---
st.set_page_config(layout="wide", page_title="OrbitGuard | CAS Core", page_icon="🛰️")

# Force "Mission Control" visual style
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #00ff41; }
    
    /* Input Fields */
    .stNumberInput input { background-color: #111; color: #00ff41; border: 1px solid #333; }
    
    /* Metrics */
    div.stMetric {
        background-color: #050505;
        border: 1px solid #1f2937;
        padding: 15px;
        border-radius: 4px;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.1);
    }
    
    /* Typography */
    h1, h2, h3 { color: #e5e7eb; font-family: 'Courier New', monospace; letter-spacing: -1px; }
    p, label { font-family: 'Courier New', monospace; }
</style>
""", unsafe_allow_html=True)

# --- 2. PHYSICS ENGINE (THE BACKEND) ---
@st.cache_resource
def get_ephemeris():
    # Load physical constants
    url = 'https://celestrak.org/NORAD/elements/stations.txt'
    try:
        sats = load.tle_file(url)
        return {s.name: s for s in sats}, "LINK ESTABLISHED"
    except:
        # Emergency Fallback TLE
        ts = load.timescale()
        line1 = "1 25544U 98067A   24143.42848900  .00014603  00000+0  26343-3 0  9997"
        line2 = "2 25544  51.6398 108.6657 0004149 105.1328 344.2093 15.50346123455086"
        iss = EarthSatellite(line1, line2, 'ISS (ZARYA)', ts)
        return {'ISS (ZARYA)': iss}, "OFFLINE MODE"

def solve_hohmann_transfer(r1, r2):
    """
    CAS FUNCTION: Solves the Vis-Viva Equation for orbital transfer.
    Returns the Delta-V (Fuel) required and the Transfer Orbit geometry.
    """
    mu = 398600  # Earth Gravitational Parameter (km^3/s^2)
    
    # Physics: Velocities
    v1 = np.sqrt(mu / r1) # Initial Velocity
    v2 = np.sqrt(mu / r2) # Final Velocity
    
    # Transfer Ellipse
    a_transfer = (r1 + r2) / 2
    v_perigee = np.sqrt(mu * (2/r1 - 1/a_transfer))
    v_apogee = np.sqrt(mu * (2/r2 - 1/a_transfer))
    
    # The "Burns" (Delta V)
    dv1 = abs(v_perigee - v1)
    dv2 = abs(v2 - v_apogee)
    total_dv = dv1 + dv2
    
    return total_dv, dv1, dv2

# --- 3. THE UI LAYER ---

# Sidebar: Controls
st.sidebar.title("ACCESS TERMINAL")
sat_data, status = get_ephemeris()
target_name = st.sidebar.selectbox("Active Asset", ["ISS (ZARYA)", "HST", "TIANGONG"])
mode = st.sidebar.radio("Operation Mode", ["Live Telemetry", "Flight Computer (CAS)"])

ts = load.timescale()
# CRITICAL FIX: Use timezone-aware datetime to prevent crash
t_now = ts.from_datetime(datetime.now(timezone.utc))

sat = sat_data.get(target_name, sat_data['ISS (ZARYA)'])

# Header
c1, c2 = st.columns([3, 1])
with c1:
    st.title(f"// {target_name}")
    st.caption("ORBITGUARD DEFENSE GRID v4.0")
with c2:
    st.metric("CONN_STATUS", status)

if mode == "Live Telemetry":
    # --- LIVE MODE (Tracking) ---
    
    # Physics: Calculate Position
    geocentric = sat.at(t_now)
    subpoint = wgs84.subpoint(geocentric)
    
    # Visualization: 3D Globe
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("ORBITAL STATE VECTOR")
        
        # Generate Ground Track (Future Path)
        minutes = np.arange(0, 90, 1)
        times = ts.from_datetime(datetime.now(timezone.utc) + timedelta(minutes=1) * minutes[:, None])
        # Flatten the times array for Skyfield
        times_flat = times.flatten()
        
        path_geo = sat.at(times_flat)
        path_sub = wgs84.subpoint(path_geo)
        
        fig = go.Figure()
        
        # 1. Earth
        fig.add_trace(go.Scattergeo(
            lon=path_sub.longitude.degrees, lat=path_sub.latitude.degrees,
            mode='lines', line=dict(width=2, color='#00ff41'),
            name='Projected Path'
        ))
        
        # 2. Satellite
        fig.add_trace(go.Scattergeo(
            lon=[subpoint.longitude.degrees], lat=[subpoint.latitude.degrees],
            mode='markers', marker=dict(size=12, color='white', symbol='diamond'),
            name=target_name
        ))
        
        fig.update_geos(
            projection_type="orthographic",
            showland=True, landcolor="#111", oceancolor="#000",
            showcountries=False, showlakes=False
        )
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            paper_bgcolor="#00000000",
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("TELEMETRY")
        st.metric("ALTITUDE", f"{subpoint.elevation.km:.2f} km")
        st.metric("LATITUDE", f"{subpoint.latitude.degrees:.4f}°")
        st.metric("LONGITUDE", f"{subpoint.longitude.degrees:.4f}°")
        st.info("System calculating orbital perturbations via SGP4 propagation model.")

elif mode == "Flight Computer (CAS)":
    # --- CAS MODE (Problem Solving) ---
    st.markdown("### 🚀 HOHMANN TRANSFER SOLVER")
    st.markdown("Calculate the fuel required to move this satellite to a new orbit.")
    
    # Inputs
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        current_r = 6378 + 420 # Approx LEO
        st.metric("CURRENT ORBIT RADIUS (r1)", f"{current_r} km")
    with col_in2:
        target_alt = st.number_input("TARGET ALTITUDE (km)", value=35786) # Geo Sync
        target_r = 6378 + target_alt
    
    # The CAS Logic (Math)
    total_dv, burn1, burn2 = solve_hohmann_transfer(current_r, target_r)
    
    # Visualization: The Transfer Orbit
    theta = np.linspace(0, 2*np.pi, 100)
    
    # Circle 1 (Start)
    x1 = current_r * np.cos(theta)
    y1 = current_r * np.sin(theta)
    
    # Circle 2 (Target)
    x2 = target_r * np.cos(theta)
    y2 = target_r * np.sin(theta)
    
    # Ellipse (Transfer)
    a = (current_r + target_r) / 2 # Semi-major axis
    # Shift ellipse so focus is at (0,0) - Earth Center
    c = a - current_r 
    # Parametric ellipse equations
    b = np.sqrt(a**2 - c**2) # Semi-minor axis (approx for viz)
    
    # Plotting the "Solution"
    fig_orbit = go.Figure()
    
    # Earth (Center)
    fig_orbit.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=20, color='blue'), name='Earth'))
    
    # Orbits
    fig_orbit.add_trace(go.Scatter(x=x1, y=y1, mode='lines', line=dict(color='green', dash='dash'), name='Initial Orbit'))
    fig_orbit.add_trace(go.Scatter(x=x2, y=y2, mode='lines', line=dict(color='red', dash='dash'), name='Target Orbit'))
    
    fig_orbit.update_layout(
        plot_bgcolor="#000", paper_bgcolor="#000",
        xaxis=dict(showgrid=False, visible=False), 
        yaxis=dict(showgrid=False, visible=False, scaleanchor="x", scaleratio=1),
        margin=dict(l=20, r=20, t=20, b=20),
        height=400
    )
    
    # Results Dashboard
    r1, r2 = st.columns([2, 1])
    with r1:
        st.plotly_chart(fig_orbit, use_container_width=True)
    with r2:
        st.success(f"TOTAL DELTA-V: {total_dv:.3f} km/s")
        st.write("---")
        st.write(f"**BURN 1 (Injection):** {burn1:.3f} km/s")
        st.write(f"**BURN 2 (Circularize):** {burn2:.3f} km/s")
        st.caption("Calculated using Vis-Viva Equation")
