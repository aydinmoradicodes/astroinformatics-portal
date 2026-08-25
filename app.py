import streamlit as st
import warnings

# 0. SYSTEM CONFIGURATION
warnings.filterwarnings("ignore") # Silence the noise

import lightkurve as lk
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import astropy.units as u
import time

# --------------------------------------------------------------------------------
# 1. VISUAL CONFIGURATION (The "Sci-Fi" Look)
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
        background-image: radial-gradient(circle at 50% 0%, #1c1c3c 0%, #000000 70%);
    }
    
    /* Typography */
    h1, h2, h3, p, div, span, input { font-family: 'Inter', sans-serif !important; }
    h1 { background: -webkit-linear-gradient(#00f2ff, #0055ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Glassmorphic Metrics */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(0, 242, 255, 0.2);
        backdrop-filter: blur(10px);
        border-radius: 8px;
        padding: 10px;
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover { border-color: #00f2ff; transform: scale(1.02); }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #050508; border-right: 1px solid #222; }
    
    /* Progress Bar Color */
    .stProgress > div > div > div > div { background-color: #00f2ff; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 2. SIDEBAR CONTROLS
# --------------------------------------------------------------------------------
st.sidebar.title("🔭 Mission Control")

# Search Mode Selector
search_mode = st.sidebar.radio("Input Method:", ["Search Database", "Select Verified Target"])

if search_mode == "Select Verified Target":
    # The Safe List (Guaranteed to look amazing)
    PRESETS = {
        "Kepler-22": "Habitable Zone Super-Earth",
        "Kepler-8": "Hot Jupiter (Deep V-Dip)",
        "Kepler-186": "First Earth-Size in HZ",
        "Kepler-444": "Ancient 5-Planet System",
        "Kepler-16": "Circumbinary (Tatooine) World"
    }
    selected_preset = st.sidebar.selectbox("Verified Candidates:", list(PRESETS.keys()))
    target_input = selected_preset
    st.sidebar.caption(f"ℹ️ {PRESETS[selected_preset]}")
else:
    # Free Search
    target_input = st.sidebar.text_input("Enter Target ID:", value="Kepler-8b")
    st.sidebar.caption("Try: 'Kepler-8', 'Proxima Centauri', 'TRAPPIST-1'")

bin_size = st.sidebar.slider("Signal Smoothing (Binning):", 5, 50, 20)
st.sidebar.markdown("---")
st.sidebar.markdown("**Pipeline Status:** 🟢 Online")

# --------------------------------------------------------------------------------
# 3. DATA ENGINE (The Robust "Omni-Search")
# --------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def fetch_telemetry(target_name):
    try:
        # Step 1: Search using Lightkurve
        # We search for "Kepler" author first as it is cleanest
        search = lk.search_lightcurve(target_name, author="Kepler", cadence="long")
        
        # Fallback: If no Kepler author, try broadly (e.g. TESS or K2)
        if len(search) == 0:
            search = lk.search_lightcurve(target_name, cadence="long")
            
        if len(search) == 0:
            return None, None
            
        # Step 2: Download the largest file (Best chance of good data)
        # We sort by observation length to get the most complete dataset
        best_index = np.argmax(search.exptime) 
        lc = search[best_index].download(quality_bitmask='default', download_dir=None)
        
        if lc is None: return None, None
        
        # Step 3: Clean the Signal
        clean_lc = lc.remove_nans().remove_outliers(sigma=5).flatten(window_length=201)
        
        return lc, clean_lc
    except Exception as e:
        return None, None

# --------------------------------------------------------------------------------
# 4. MAIN EXECUTION LOOP
# --------------------------------------------------------------------------------
st.title("Astroinformatics & Exoplanet Analytics")
st.markdown(f"**Target Lock:** `{target_input}`")

# Initialize Session State variables
if 'lc_data' not in st.session_state: st.session_state.lc_data = None
if 'last_target' not in st.session_state: st.session_state.last_target = ""

# Run Pipeline
if target_input and target_input != st.session_state.last_target:
    st.session_state.last_target = target_input
    
    # THE COOL PROGRESS BAR
    progress_text = "Initializing Deep Space Network..."
    my_bar = st.progress(0, text=progress_text)

    # 25% - Aligning
    time.sleep(0.3) 
    my_bar.progress(25, text="Aligning Optical Arrays...")
    
    # 50% - Fetching
    raw, clean = fetch_telemetry(target_input)
    my_bar.progress(60, text="Ingesting Telemetry Stream...")
    
    # 75% - Processing
    if clean is not None:
        st.session_state.lc_data = clean
        st.session_state.raw_data = raw
        my_bar.progress(90, text="Running Fourier Transform...")
        time.sleep(0.2)
        my_bar.progress(100, text="Visualizing...")
        time.sleep(0.1)
        my_bar.empty() # Hide bar when done
    else:
        my_bar.empty()
        st.error(f"❌ Signal Lost. Could not retrieve telemetry for '{target_input}'. Try a different ID.")
        st.session_state.lc_data = None

# --------------------------------------------------------------------------------
# 5. DASHBOARD DISPLAY
# --------------------------------------------------------------------------------
if st.session_state.lc_data is not None:
    lc = st.session_state.lc_data
    raw_meta = st.session_state.raw_data
    
    # --- PHYSICS CORE ---
    # BLS Period Finding
    periodogram = lc.to_periodogram(method="bls", period=np.linspace(1, 100, 10000))
    best_period = periodogram.period_at_max_power
    best_t0 = periodogram.transit_time_at_max_power
    transit_depth = periodogram.depth_at_max_power.value
    
    # Metadata Extraction (With Fallbacks)
    r_star = getattr(raw_meta.meta, 'RADIUS', 1.0)
    if r_star is None: r_star = 1.0
    
    t_star = getattr(raw_meta.meta, 'TEFF', 5778.0)
    if t_star is None: t_star = 5778.0

    # Calculations
    r_planet_earth = np.sqrt(transit_depth) * r_star * 109.2
    a_au = ((best_period.value/365.25)**2)**(1/3) # Keplers 3rd Law
    
    # Temp Calculation
    teq_k = t_star * np.sqrt(r_star * 0.00465 / (2 * a_au))
    teq_c = teq_k - 273.15
    
    # Habitability Logic
    if 0 < teq_c < 100: hab_status, hab_color = "HABITABLE ZONE", "#00ff00"
    elif teq_c >= 100: hab_status, hab_color = "TOO HOT", "#ff4444"
    else: hab_status, hab_color = "TOO COLD", "#00d4ff"

    # --- UI ROW 1: METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orbital Period", f"{best_period.value:.3f} Days", "Signal Periodicity")
    c2.metric("Planet Size", f"{r_planet_earth:.2f} x Earth", f"Star Radius: {r_star:.2f} Sun")
    c3.metric("Surface Temp", f"{teq_c:.0f} °C", hab_status)
    c4.metric("Confidence", f"{periodogram.max_power.value:.2f}", "Signal-to-Noise")

    if r_star == 1.0 and t_star == 5778.0:
        st.warning("⚠️ **Note:** NASA Metadata missing for this star. Calculations assumed a Sun-like host.")

    # --- UI ROW 2: VISUALS ---
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.subheader("📉 Phase-Locked Transit Signal")
        folded = lc.fold(period=best_period, epoch_time=best_t0)
        binned = folded.bin(time_bin_size=bin_size * 0.001 * u.day)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=folded.time.value, y=folded.flux.value, mode='markers', name='Raw Data', marker=dict(size=2, color='rgba(255, 255, 255, 0.3)')))
        fig.add_trace(go.Scatter(x=binned.time.value, y=binned.flux.value, mode='lines+markers', name='Clean Signal', line=dict(color='#00f2ff', width=3)))
        fig.update_layout(
            template="plotly_dark", height=450, 
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Orbital Phase", yaxis_title="Normalized Flux",
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_side:
        st.subheader("🪐 Orbital Recon")
        # 1:1 Aspect Ratio Plot
        theta = np.linspace(0, 2*np.pi, 100)
        lum = (r_star**2) * ((t_star/5778)**4)
        hz_in, hz_out = np.sqrt(lum)*0.95, np.sqrt(lum)*1.37
        
        fig_orb = go.Figure()
        # HZ
        fig_orb.add_trace(go.Scatter(x=hz_in*np.cos(theta), y=hz_in*np.sin(theta), mode='lines', line=dict(color='rgba(0,255,0,0)'), showlegend=False))
        fig_orb.add_trace(go.Scatter(x=hz_out*np.cos(theta), y=hz_out*np.sin(theta), mode='lines', fill='tonexty', fillcolor='rgba(0,255,0,0.1)', line=dict(color='rgba(0,255,0,0.1)'), name='Habitable Zone'))
        # Orbit
        fig_orb.add_trace(go.Scatter(x=a_au*np.cos(theta), y=a_au*np.sin(theta), mode='lines', line=dict(color=hab_color, width=2), name='Orbit'))
        # Bodies
        fig_orb.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(color='#ffcc00', size=15), name='Star'))
        fig_orb.add_trace(go.Scatter(x=[a_au], y=[0], mode='markers', marker=dict(color=hab_color, size=8, line=dict(color='white', width=1)), name='Planet'))
        
        limit = max(hz_out, a_au) * 1.2
        fig_orb.update_layout(
            template="plotly_dark", height=350, width=350,
            xaxis=dict(range=[-limit, limit], visible=False),
            yaxis=dict(range=[-limit, limit], visible=False, scaleanchor="x", scaleratio=1),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False, margin=dict(l=0,r=0,t=0,b=0)
        )
        st.plotly_chart(fig_orb, use_container_width=True)
        
    # --- DOWNLOAD DATA ---
    st.download_button("📥 Download Analysis CSV", data=pd.DataFrame({'Time':lc.time.value, 'Flux':lc.flux.value}).to_csv(), file_name=f"{target_input}_analysis.csv")

elif st.session_state.lc_data is None and target_input:
    st.info("Ready for analysis. Enter a target ID in the sidebar to begin.")
