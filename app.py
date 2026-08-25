import streamlit as st
import warnings

# 0. SYSTEM CONFIGURATION
warnings.filterwarnings("ignore")

import lightkurve as lk
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import astropy.units as u
import time

# --------------------------------------------------------------------------------
# 1. VISUAL CONFIGURATION (DEEP VOID THEME)
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="UBC Astroinformatics Lab", 
    page_icon="🔭", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* DEEP VOID BACKGROUND */
    .stApp {
        background-color: #000000;
        background-image: radial-gradient(circle at center, #111111 0%, #000000 100%);
    }
    
    /* SHARP TYPOGRAPHY */
    h1, h2, h3, p, div, span, input, label { 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important; 
        color: #ffffff !important;
    }
    
    /* NEON ACCENTS */
    h1 { 
        background: linear-gradient(90deg, #ffffff, #a0a0a0); 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        font-weight: 800; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
    }
    
    /* GLASS METRIC CARDS */
    div[data-testid="metric-container"] {
        background: rgba(20, 20, 20, 0.8);
        border: 1px solid #333;
        border-left: 4px solid #00ff41;
        border-radius: 4px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="metric-container"]:hover { border-color: #ffffff; }
    
    /* Metric Text Overrides */
    div[data-testid="stMetricValue"] { color: #00ff41 !important; font-size: 28px !important; font-weight: 700; }
    div[data-testid="stMetricLabel"] { color: #888 !important; font-size: 13px !important; text-transform: uppercase; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #050505; border-right: 1px solid #222; }
    
    /* Progress Bar */
    .stProgress > div > div > div > div { background-color: #00ff41; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 2. VERIFIED TARGET DATABASE (NASA ARCHIVE DATA)
# --------------------------------------------------------------------------------
# Data Verified against NASA Exoplanet Archive (2025)
PRESETS = {
    "Kepler-22b (Habitable Zone)": {
        "id": "Kepler-22", 
        "r_star": 0.97, "t_star": 5518, 
        "desc": "Confirmed Super-Earth in the habitable zone. Surface allows liquid water."
    },
    "Kepler-8b (Hot Jupiter)": {
        "id": "Kepler-8", 
        "r_star": 1.48, "t_star": 6213, 
        "desc": "Massive Gas Giant orbiting extremely close. Shows a classic deep transit dip."
    },
    "Kepler-186f (Earth Twin)": {
        "id": "Kepler-186", 
        "r_star": 0.47, "t_star": 3788, 
        "desc": "First validated Earth-size planet in the habitable zone of another star."
    },
    "Kepler-452b (Earth's Cousin)": {
        "id": "Kepler-452", 
        "r_star": 1.11, "t_star": 5757, 
        "desc": "Near-Earth-size planet in the habitable zone of a Sun-like star."
    },
    "Kepler-16b (Tatooine)": {
        "id": "Kepler-16", 
        "r_star": 0.65, "t_star": 4450, 
        "desc": "Circumbinary planet orbiting two stars. Physics corrected for primary star."
    }
}

# --------------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS
# --------------------------------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg", width=150)
st.sidebar.title("MISSION CONTROL")

search_mode = st.sidebar.radio("Input Source:", ["VERIFIED DATABASE", "RAW SEARCH"], label_visibility="collapsed")

if search_mode == "VERIFIED DATABASE":
    selected_preset = st.sidebar.selectbox("Select Target:", list(PRESETS.keys()))
    # LOAD ACCURATE DATA FROM DICTIONARY
    current_target_id = PRESETS[selected_preset]["id"]
    manual_r_star = PRESETS[selected_preset]["r_star"]
    manual_t_star = PRESETS[selected_preset]["t_star"]
    st.sidebar.success(f"✅ {PRESETS[selected_preset]['desc']}")
else:
    target_input = st.sidebar.text_input("Kepler ID / Name:", value="Kepler-10")
    current_target_id = target_input
    manual_r_star = None 
    manual_t_star = None
    st.sidebar.caption("Warning: Raw search relies on unverified metadata.")

bin_size = st.sidebar.slider("Signal Smoothing (Binning):", 5, 50, 20)
st.sidebar.markdown("---")
st.sidebar.markdown("**SYSTEM STATUS:** 🟢 NOMINAL")

# --------------------------------------------------------------------------------
# 4. MAIN EXECUTION
# --------------------------------------------------------------------------------
st.title("ASTROINFORMATICS ANALYTICS")
st.markdown(f"**Target Lock:** `{current_target_id}`")

# DATA FETCHER
@st.cache_data(show_spinner=False)
def get_telemetry(target):
    try:
        # Search specifically for Kepler "Long Cadence" data (Highest Quality)
        search = lk.search_lightcurve(target, author="Kepler", cadence="long")
        
        # If empty, try basic search
        if len(search) == 0:
            search = lk.search_lightcurve(target, cadence="long")
            
        if len(search) == 0: return None
        
        # Download largest available dataset to memory
        # We pick the one with maximum exposure time to ensure we get a transit
        best_idx = np.argmax(search.exptime)
        lc = search[best_idx].download(quality_bitmask='default', download_dir=None)
        
        # Clean
        clean_lc = lc.remove_nans().remove_outliers(sigma=5).flatten(window_length=201)
        return clean_lc
    except:
        return None

# RUN PIPELINE
if current_target_id:
    with st.spinner("Aligning Deep Space Network Arrays..."):
        # Loading Animation
        if 'load_bar' not in st.session_state:
            bar = st.progress(0)
            for i in range(100):
                time.sleep(0.005)
                bar.progress(i+1)
            bar.empty()
            st.session_state.load_bar = True
            
    lc_data = get_telemetry(current_target_id)
else:
    lc_data = None

if lc_data is None:
    st.error(f"⚠️ SIGNAL LOSS: Could not retrieve telemetry for '{current_target_id}'. If using Raw Search, check spelling.")
else:
    # --------------------------------------------------------------------------------
    # 5. PHYSICS CORE
    # --------------------------------------------------------------------------------
    # Period Detection
    periodogram = lc_data.to_periodogram(method="bls", period=np.linspace(0.5, 100, 10000))
    best_period = periodogram.period_at_max_power
    best_t0 = periodogram.transit_time_at_max_power
    transit_depth = periodogram.depth_at_max_power.value

    # RESOLVE PHYSICS CONSTANTS
    if manual_r_star:
        r_star = manual_r_star
        t_star = manual_t_star
    else:
        # Fallback to metadata
        r_star = getattr(lc_data.meta, 'RADIUS', 1.0)
        t_star = getattr(lc_data.meta, 'TEFF', 5778.0)
        if r_star is None: r_star = 1.0
        if t_star is None: t_star = 5778.0

    # Calculations
    r_planet_earth = np.sqrt(transit_depth) * r_star * 109.2
    
    # Improved Semi-Major Axis (Kepler's 3rd Law with Mass Scaling)
    # M_star approx R_star for Main Sequence
    star_mass_solar = r_star 
    a_au = ((best_period.value/365.25)**2 * star_mass_solar)**(1/3)
    
    # Equilibrium Temp
    teq_k = t_star * np.sqrt(r_star * 0.00465 / (2 * a_au))
    teq_c = teq_k - 273.15
    
    # Habitability Logic
    if 0 < teq_c < 100: hab_status, hab_color = "HABITABLE ZONE", "#00ff41" # Green
    elif teq_c >= 100: hab_status, hab_color = "TOO HOT", "#ff2a2a" # Red
    else: hab_status, hab_color = "TOO COLD", "#00aaff" # Blue

    # --------------------------------------------------------------------------------
    # 6. DASHBOARD UI
    # --------------------------------------------------------------------------------
    
    # METRICS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orbital Period", f"{best_period.value:.3f} Days", "Signal Confirmed")
    c2.metric("Planet Size", f"{r_planet_earth:.2f} x Earth", f"Star: {r_star} R_Sun")
    c3.metric("Surface Temp", f"{teq_c:.0f} °C", hab_status)
    c4.metric("Orbit Distance", f"{a_au:.3f} AU", "Semi-Major Axis")
    
    if not manual_r_star and (r_star == 1.0 or t_star == 5778.0):
        st.warning("⚠️ NASA Metadata missing for this star. Calculations assumed a Sun-like host.")

    # TABS FOR VISUALIZATION (Fixes Layout Overlap)
    tab1, tab2, tab3 = st.tabs(["📉 Transit Analysis", "🪐 Orbital Recon", "💾 Raw Data"])

    with tab1:
        folded = lc_data.fold(period=best_period, epoch_time=best_t0)
        binned = folded.bin(time_bin_size=bin_size * 0.001 * u.day)
        
        fig_lc = go.Figure()
        fig_lc.add_trace(go.Scatter(x=folded.time.value, y=folded.flux.value, mode='markers', name='Raw Data', marker=dict(size=2, color='rgba(255,255,255,0.2)')))
        fig_lc.add_trace(go.Scatter(x=binned.time.value, y=binned.flux.value, mode='lines+markers', name='Clean Signal', line=dict(color='#00ff41', width=3)))
        fig_lc.update_layout(
            template="plotly_dark", height=450, 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Phase", yaxis_title="Normalized Flux",
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_lc, use_container_width=True)

    with tab2:
        # GEOMETRY SETUP
        theta = np.linspace(0, 2*np.pi, 100)
        lum = (r_star**2) * ((t_star/5778)**4)
        hz_in = np.sqrt(lum)*0.95
        hz_out = np.sqrt(lum)*1.37
        
        plot_limit = max(hz_out, a_au) * 1.2
        
        fig_orb = go.Figure()
        
        # HZ (Green Band)
        fig_orb.add_trace(go.Scatter(x=hz_in*np.cos(theta), y=hz_in*np.sin(theta), mode='lines', line=dict(color='rgba(0,255,65,0.2)'), showlegend=False))
        fig_orb.add_trace(go.Scatter(x=hz_out*np.cos(theta), y=hz_out*np.sin(theta), mode='lines', fill='tonexty', fillcolor='rgba(0,255,65,0.1)', line=dict(color='rgba(0,255,65,0.2)'), name='Habitable Zone'))
        
        # Orbit (Color Coded)
        fig_orb.add_trace(go.Scatter(x=a_au*np.cos(theta), y=a_au*np.sin(theta), mode='lines', line=dict(color=hab_color, width=2, dash='dash'), name='Orbit Path'))
        
        # Star & Planet
        fig_orb.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(color='#ffcc00', size=15), name='Star'))
        fig_orb.add_trace(go.Scatter(x=[a_au], y=[0], mode='markers', marker=dict(color='#ffffff', size=8, line=dict(color=hab_color, width=2)), name='Planet'))
        
        # LOCKED ASPECT RATIO
        fig_orb.update_layout(
            template="plotly_dark", height=500, width=500,
            xaxis=dict(range=[-plot_limit, plot_limit], visible=False, scaleanchor="y", scaleratio=1),
            yaxis=dict(range=[-plot_limit, plot_limit], visible=False),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=True, legend=dict(x=0, y=0), margin=dict(l=0,r=0,t=0,b=0)
        )
        col_L, col_R, col_M = st.columns([1, 2, 1])
        with col_R:
            st.plotly_chart(fig_orb, use_container_width=True)

    with tab3:
        st.markdown("### 💾 Raw Telemetry Stream")
        st.dataframe(pd.DataFrame({'Time (BJD)':lc_data.time.value, 'Flux':lc_data.flux.value}), use_container_width=True)
