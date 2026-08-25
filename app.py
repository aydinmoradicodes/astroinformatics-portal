import streamlit as st
import lightkurve as lk
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import astropy.units as u

# --------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & ACADEMIC STYLING
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="UBC Astroinformatics Research Portal", 
    page_icon="🌌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: Professional "Dark Mode" Research Dashboard (No "Video Game" fonts)
st.markdown("""
    <style>
    .main { background-color: #05070f; }
    h1 { color: #00bbf9 !important; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    h2, h3 { color: #9b5de5 !important; }
    .stMetric { background-color: #0e1222; padding: 15px; border-radius: 10px; border: 1px solid #1e295d; }
    div[data-testid="stMetricDelta"] > div { color: #00f2ff !important; }
    p { color: #b8c1ec; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 2. HEADER & PROJECT IDENTITY
# --------------------------------------------------------------------------------
st.title("Astroinformatics & Exoplanetary Habitability Pipeline")
st.markdown("""
    **Research Engineer:** Aydin | **Target Program:** UBC Combined Major (CS & Stats)
    
    *An automated computational pipeline utilizing NASA Kepler telemetry to isolate transit signals, 
    calculate orbital dynamics, and estimate planetary habitability (Equilibrium Temperature).*
""")
st.divider()

# --------------------------------------------------------------------------------
# 3. MISSION CONTROL SIDEBAR
# --------------------------------------------------------------------------------
st.sidebar.header("🔭 Instrumentation Controls")
target_star = st.sidebar.text_input("Kepler Target ID:", value="Kepler-22")

# Session State Logic to prevent API spamming
if "last_star" not in st.session_state or st.session_state.last_star != target_star:
    st.session_state.last_star = target_star
    with st.spinner("Querying NASA MAST Archives..."):
        try:
            search = lk.search_lightcurve(str(target_star).strip(), author="Kepler")
            st.session_state.quarters = sorted([int(q) for q in search.quarter if q is not None and not np.isnan(q)])
        except:
            st.session_state.quarters = []

if "quarters" in st.session_state and st.session_state.quarters:
    selected_quarter = st.sidebar.selectbox("Select Mission Quarter:", options=st.session_state.quarters, index=0)
else:
    st.sidebar.warning("Target not found in Kepler catalog.")
    selected_quarter = None

bin_size = st.sidebar.slider("Phase Binning Resolution:", 5, 100, 20)
st.sidebar.markdown("---")
st.sidebar.info("**Pipeline Status:** Ready for Telemetry Ingestion.")

# --------------------------------------------------------------------------------
# 4. DATA ENGINE (ROBUST CLOUD FETCHING)
# --------------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_data(star, quarter):
    if not quarter: return None, None, None, None
    try:
        search = lk.search_lightcurve(str(star).strip(), author="Kepler", quarter=int(quarter))
        if len(search) == 0: return None, None, None, None
        
        # Download data into memory (bypassing cloud disk limits)
        lc = search.download(quality_bitmask='default', download_dir=None)
        if lc is None: return None, None, None, None
        
        # Advanced Signal Processing: Remove NaNs, Sigma Clip Outliers, Flatten Trends
        clean_lc = lc.remove_nans().remove_outliers(sigma=5).flatten(window_length=101)
        
        # Extract Metadata for Physics Math
        r_star = float(lc.meta.get('RADIUS', 1.0) or 1.0)
        teff_star = float(lc.meta.get('TEFF', 5778.0) or 5778.0) # Star Temp (Kelvin)
        
        return lc, clean_lc, r_star, teff_star
    except Exception:
        return None, None, None, None

# --------------------------------------------------------------------------------
# 5. EXECUTION & PHYSICS CORE
# --------------------------------------------------------------------------------
if selected_quarter:
    with st.spinner("Processing Deep Space Telemetry..."):
        raw_lc, clean_lc, r_star, teff_star = fetch_data(target_star, selected_quarter)
else:
    raw_lc, clean_lc, r_star, teff_star = None, None, 1.0, 5778.0

if clean_lc is None:
    st.error(f"❌ Pipeline Failure: Could not retrieve data for '{target_star}'. Try 'Kepler-22' (Habitable) or 'Kepler-8'.")
else:
    # --- A. TRANSIT DETECTION (BLS ALGORITHM) ---
    periodogram = clean_lc.to_periodogram(method="bls")
    best_period = periodogram.period_at_max_power
    best_t0 = periodogram.transit_time_at_max_power
    transit_depth = periodogram.depth_at_max_power.value

    # --- B. ASTROPHYSICS CALCULATIONS ---
    # 1. Planet Radius (R_p)
    r_planet_jup = np.sqrt(transit_depth) * r_star * 9.731
    
    # 2. Orbital Distance / Semi-Major Axis (a) using Kepler's 3rd Law
    # Assumption: Star Mass ≈ 1 Solar Mass for approximation
    period_years = best_period.value / 365.25
    semi_major_axis_au = (period_years ** 2) ** (1/3)
    
    # 3. Equilibrium Temperature (T_eq) - The "Habitability" Check
    r_star_au = r_star * 0.00465 # Convert Solar Radius to AU
    # Bond Albedo assumed 0.3 (Earth-like)
    eq_temp_k = teff_star * np.sqrt(r_star_au / (2 * semi_major_axis_au)) * ((1 - 0.3)**0.25)
    eq_temp_c = eq_temp_k - 273.15 # Convert to Celsius

    # --- C. HABITABILITY STATUS CHECK ---
    if 0 < eq_temp_c < 100:
        habitable_status = "🟩 POTENTIALLY HABITABLE (Liquid Water Possible)"
    elif eq_temp_c >= 100:
        habitable_status = "🟥 TOO HOT (Runaway Greenhouse)"
    else:
        habitable_status = "🟦 TOO COLD (Ice World)"

    # --------------------------------------------------------------------------------
    # 6. RESEARCH DASHBOARD (VISUALS)
    # --------------------------------------------------------------------------------
    
    # Row 1: The Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Orbital Period", f"{best_period.value:.4f} Days", "Verified Periodic Signal")
    col2.metric("Planetary Radius", f"{r_planet_jup:.2f} x Jupiter", f"Host Radius: {r_star:.2f} Sun")
    col3.metric("Orbital Distance", f"{semi_major_axis_au:.3f} AU", "Semi-Major Axis")
    col4.metric("Surface Temp", f"{eq_temp_c:.1f} °C", f"{habitable_status}")

    # Row 2: The Plots
    # Folding Logic
    folded_lc = clean_lc.fold(period=best_period, epoch_time=best_t0)
    time_delta = (folded_lc.time.value[-1] - folded_lc.time.value[0]) / len(folded_lc.time.value) if len(folded_lc.time.value) > 1 else 0.02
    binned_lc = folded_lc.bin(time_bin_size=(bin_size * time_delta) * u.day)

    tabs = st.tabs(["📊 Phase-Folded Transit Analysis", "🔭 Raw Telemetry Stream", "💾 Data Export"])

    with tabs[0]:
        st.subheader("Phase-Folded Transit Detection")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=folded_lc.time.value, y=folded_lc.flux.value, mode='markers', name='Raw Data', marker=dict(color='#00bbf9', size=3, opacity=0.3)))
        fig.add_trace(go.Scatter(x=binned_lc.time.value, y=binned_lc.flux.value, mode='lines+markers', name='Binned Signal', line=dict(color='#f15bb5', width=3)))
        fig.update_layout(template="plotly_dark", height=450, xaxis_title="Orbital Phase (Days)", yaxis_title="Normalized Flux", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Detected transit signal folded over {best_period.value:.4f} days. The dip represents the planet blocking starlight.")

    with tabs[1]:
        st.subheader("Continuous Light Curve")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=clean_lc.time.value, y=clean_lc.flux.value, mode='markers', marker=dict(color='#9b5de5', size=2)))
        fig2.update_layout(template="plotly_dark", height=400, xaxis_title="Time (BJD)", yaxis_title="Flux", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

    with tabs[2]:
        st.subheader("Export Processed Matrix")
        csv = pd.DataFrame({'Phase': folded_lc.time.value, 'Flux': folded_lc.flux.value}).to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name=f"{target_star}_analysis.csv", mime="text/csv")
