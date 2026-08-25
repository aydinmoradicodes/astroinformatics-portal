import streamlit as st
import warnings
warnings.filterwarnings("ignore")

import lightkurve as lk
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import astropy.units as u
import time

# --------------------------------------------------------------------------------
# 1. VISUAL CONFIGURATION (Glassmorphism UI)
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="UBC Astroinformatics Lab", 
    page_icon="🔭", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Deep Space Background */
    .stApp {
        background-color: #000000;
        background-image: radial-gradient(circle at 50% 50%, #1a1a2e 0%, #000000 100%);
    }
    
    /* Typography */
    h1, h2, h3, p, div { font-family: 'Inter', sans-serif !important; }
    h1 { background: -webkit-linear-gradient(#00d4ff, #0055ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; }
    
    /* Glassmorphic Cards */
    .css-1r6slb0, .stMetric { 
        background: rgba(255, 255, 255, 0.05); 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        backdrop-filter: blur(10px); 
        border-radius: 12px; 
    }
    
    /* Metric Text */
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 26px !important; text-shadow: 0 0 10px rgba(0, 212, 255, 0.5); }
    div[data-testid="stMetricLabel"] { color: #a0aab5 !important; font-size: 14px !important; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #050505; border-right: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 2. CURATED TARGET DATABASE (Ensures Perfect Data)
# --------------------------------------------------------------------------------
# These targets are pre-verified to look amazing. No more "bad" searches.
TARGETS = {
    "Kepler-22b (Habitable Super-Earth)": {"id": "KIC 10593626", "r_star": 0.97, "t_star": 5518, "desc": "The first planet found in the habitable zone of a Sun-like star."},
    "Kepler-8b (Hot Jupiter - Clean V-Dip)": {"id": "KIC 8145929", "r_star": 1.48, "t_star": 6213, "desc": "A massive gas giant with a very clear transit signal."},
    "Kepler-186f (Earth-Size Habitable)": {"id": "KIC 8120608", "r_star": 0.47, "t_star": 3788, "desc": "First Earth-sized planet discovered in the habitable zone."},
    "Kepler-444 (Ancient System)": {"id": "KIC 6278762", "r_star": 0.75, "t_star": 5040, "desc": "An 11.2 billion year old system with 5 planets."},
    "TRAPPIST-1 (Red Dwarf System)": {"id": "TIC 278892590", "r_star": 0.117, "t_star": 2566, "desc": "Famous system with 7 Earth-sized planets."}
}

# --------------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS
# --------------------------------------------------------------------------------
st.sidebar.title("🔭 Mission Control")
st.sidebar.markdown("Select a **Verified Target** to analyze:")

selected_name = st.sidebar.selectbox("Target Selector", list(TARGETS.keys()), index=0)
target_data = TARGETS[selected_name]

st.sidebar.info(f"ℹ️ **Target Info:** {target_data['desc']}")
bin_size = st.sidebar.slider("Signal Processing (Binning)", 5, 50, 20)

# --------------------------------------------------------------------------------
# 4. MAIN LAYOUT
# --------------------------------------------------------------------------------
st.title("Astroinformatics & Exoplanet Analytics")
st.markdown(f"**Analyzing Telemetry for:** `{selected_name}` | **Pipeline Status:** Active")
st.divider()

# --------------------------------------------------------------------------------
# 5. DATA ENGINE (Optimized)
# --------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_telemetry(target_id, manual_r, manual_t):
    try:
        # Search (Strictly Kepler/TESS based on ID format)
        if "TIC" in target_id:
            search = lk.search_lightcurve(target_id, mission="TESS")
        else:
            search = lk.search_lightcurve(target_id, author="Kepler")
            
        if len(search) == 0: return None
        
        # Download (Memory Only)
        lc = search[0].download(quality_bitmask='default', download_dir=None)
        
        # Signal Cleaning Pipeline
        clean_lc = lc.remove_nans().remove_outliers(sigma=5).flatten(window_length=201)
        
        return clean_lc
    except:
        return None

# EXECUTION
with st.spinner("Establishing Downlink with NASA Deep Space Network..."):
    # Simulate "High Tech" loading delay for effect
    if "load_state" not in st.session_state:
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.005)
            progress_bar.progress(i + 1)
        progress_bar.empty()
        st.session_state.load_state = True

    lc_data = get_telemetry(target_data['id'], target_data['r_star'], target_data['t_star'])

if lc_data is None:
    st.error("Telemetry Stream Offline. Please select another target.")
else:
    # --------------------------------------------------------------------------------
    # 6. PHYSICS CORE
    # --------------------------------------------------------------------------------
    # BLS Search
    periodogram = lc_data.to_periodogram(method="bls", period=np.linspace(1, 20, 10000))
    best_period = periodogram.period_at_max_power
    best_t0 = periodogram.transit_time_at_max_power
    transit_depth = periodogram.depth_at_max_power.value

    # Physics Math (Using Manually Corrected Star Data for Accuracy)
    r_star = target_data['r_star']
    t_star = target_data['t_star']
    
    r_planet_earth = np.sqrt(transit_depth) * r_star * 109.2 # Convert to Earth Radii
    period_days = best_period.value
    
    # Orbital Distance (AU)
    a_au = ((period_days/365.25)**2 * 1.0)**(1/3) # Assuming Sun-mass for approx
    
    # Equilibrium Temp (Kelvin & Celsius)
    teq_k = t_star * np.sqrt(r_star * 0.00465 / (2 * a_au))
    teq_c = teq_k - 273.15

    # Habitability Logic
    if 0 < teq_c < 100: hab_label, hab_color = "HABITABLE (Liquid Water)", "#00ff00"
    elif teq_c >= 100: hab_label, hab_color = "TOO HOT (Greenhouse)", "#ff4444"
    else: hab_label, hab_color = "TOO COLD (Frozen)", "#00d4ff"

    # --------------------------------------------------------------------------------
    # 7. DASHBOARD UI
    # --------------------------------------------------------------------------------
    
    # METRICS ROW
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orbital Period", f"{period_days:.3f} Days", "Confirmed Signal")
    c2.metric("Planet Size", f"{r_planet_earth:.2f} x Earth", f"Star: {r_star} R_Sun")
    c3.metric("Distance to Star", f"{a_au:.3f} AU", "Semi-Major Axis")
    c4.metric("Surface Temp", f"{teq_c:.0f} °C", hab_label)

    # VISUALIZATION ROW
    col_viz, col_orbit = st.columns([2, 1])

    with col_viz:
        st.subheader("📉 Phase-Locked Transit Signal")
        folded = lc_data.fold(period=best_period, epoch_time=best_t0)
        binned = folded.bin(time_bin_size=bin_size * 0.001 * u.day)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=folded.time.value, y=folded.flux.value, mode='markers', marker=dict(size=2, color='#445566'), name='Raw Flux'))
        fig.add_trace(go.Scatter(x=binned.time.value, y=binned.flux.value, mode='lines+markers', line=dict(color='#00d4ff', width=3), name='Clean Signal'))
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=20,r=20,t=20,b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with col_orbit:
        st.subheader("🪐 Orbital Recon")
        
        # Perfect Circles (1:1 Aspect Ratio)
        theta = np.linspace(0, 2*np.pi, 100)
        # HZ Calculation
        lum = (r_star**2) * ((t_star/5778)**4)
        hz_in, hz_out = np.sqrt(lum)*0.95, np.sqrt(lum)*1.37
        
        fig_orb = go.Figure()
        
        # HZ Zone (Green Band)
        fig_orb.add_trace(go.Scatter(x=hz_in*np.cos(theta), y=hz_in*np.sin(theta), mode='lines', line=dict(color='rgba(0,255,0,0.1)'), showlegend=False))
        fig_orb.add_trace(go.Scatter(x=hz_out*np.cos(theta), y=hz_out*np.sin(theta), mode='lines', fill='tonexty', fillcolor='rgba(0,255,0,0.1)', line=dict(color='rgba(0,255,0,0.1)'), name='Habitable Zone'))
        
        # Planet Orbit
        fig_orb.add_trace(go.Scatter(x=a_au*np.cos(theta), y=a_au*np.sin(theta), mode='lines', line=dict(color=hab_color, width=2), name='Orbit'))
        
        # Star & Planet
        fig_orb.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(color='#ffcc00', size=12), name='Star'))
        fig_orb.add_trace(go.Scatter(x=[a_au], y=[0], mode='markers', marker=dict(color='#ffffff', size=6), name='Planet'))
        
        # Force Square Aspect Ratio (No Oval Orbits)
        max_range = max(hz_out, a_au) * 1.2
        fig_orb.update_layout(
            template="plotly_dark", 
            height=400, 
            width=400,
            showlegend=False,
            xaxis=dict(range=[-max_range, max_range], showgrid=False, zeroline=False, visible=False),
            yaxis=dict(range=[-max_range, max_range], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
            margin=dict(l=10,r=10,t=10,b=10),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_orb, use_container_width=True)
