import streamlit as st
import lightkurve as lk
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import astropy.units as u

# --------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & SPACEX-STYLE UI
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="UBC Astroinformatics Research Portal", 
    page_icon="🛰️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: "SpaceX" Professional Dark Mode
st.markdown("""
    <style>
    /* Main Background: Deep Space Black */
    .main { background-color: #0b0d17; }
    
    /* Typography: Modern Sans-Serif (Aerospace Style) */
    h1, h2, h3, h4, .stMarkdown, p, div { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important; }
    
    /* Headers */
    h1 { color: #ffffff !important; font-weight: 700; letter-spacing: -0.5px; }
    h2, h3 { color: #a0aab5 !important; font-weight: 400; }
    
    /* Metric Cards: High Contrast & Flat */
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #00d4ff !important; font-weight: 600; }
    div[data-testid="stMetricLabel"] { font-size: 13px !important; color: #8d99ae !important; text-transform: uppercase; letter-spacing: 1px; }
    .stMetric { background-color: #15192b; border: 1px solid #2b3044; border-radius: 6px; padding: 15px; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #050608; border-right: 1px solid #2b3044; }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #15192b; border-radius: 4px; color: #fff; }
    .stTabs [aria-selected="true"] { background-color: #00d4ff !important; color: #000 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 2. HEADER & PROJECT IDENTITY
# --------------------------------------------------------------------------------
st.title("Astroinformatics & Exoplanetary Habitability Pipeline")
st.markdown("""
    **Principal Investigator:** Aydin | **Target Institution:** University of British Columbia (UBC)
    
    *An automated signal processing pipeline utilizing NASA Kepler telemetry to isolate transit signals, 
    simulate real-time orbital dynamics, and estimate planetary habitability potential.*
""")
st.divider()

# --------------------------------------------------------------------------------
# 3. MISSION CONTROL SIDEBAR
# --------------------------------------------------------------------------------
st.sidebar.header("🔭 Instrument Controls")
target_star = st.sidebar.text_input("Kepler Target ID:", value="Kepler-22")

# Intelligent Caching to prevent API throttling
if "last_star" not in st.session_state or st.session_state.last_star != target_star:
    st.session_state.last_star = target_star
    with st.spinner("Querying NASA MAST Archives..."):
        try:
            search = lk.search_lightcurve(str(target_star).strip(), author="Kepler")
            st.session_state.quarters = sorted([int(q) for q in search.quarter if q is not None and not np.isnan(q)])
        except:
            st.session_state.quarters = []

if "quarters" in st.session_state and st.session_state.quarters:
    selected_quarter = st.sidebar.selectbox("Mission Quarter:", options=st.session_state.quarters, index=0)
else:
    st.sidebar.warning("Target not found in Kepler catalog.")
    selected_quarter = None

bin_size = st.sidebar.slider("Phase Binning Resolution:", 5, 100, 20)
st.sidebar.markdown("---")
st.sidebar.caption("✅ **System Status:** Connected to NASA MAST")

# --------------------------------------------------------------------------------
# 4. ROBUST DATA INGESTION ENGINE
# --------------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_data(star, quarter):
    if not quarter: return None, None, None, None
    try:
        search = lk.search_lightcurve(str(star).strip(), author="Kepler", quarter=int(quarter))
        if len(search) == 0: return None, None, None, None
        
        # Download to memory (Fixes Cloud Throttling Issues)
        lc = search.download(quality_bitmask='default', download_dir=None)
        if lc is None: return None, None, None, None
        
        # Scientific Cleaning
        clean_lc = lc.remove_nans().remove_outliers(sigma=5).flatten(window_length=101)
        
        # Extract Metadata
        r_star = float(lc.meta.get('RADIUS', 1.0) or 1.0)
        teff_star = float(lc.meta.get('TEFF', 5778.0) or 5778.0)
        
        return lc, clean_lc, r_star, teff_star
    except Exception:
        return None, None, None, None

# --------------------------------------------------------------------------------
# 5. PHYSICS CORE
# --------------------------------------------------------------------------------
if selected_quarter:
    with st.spinner("Processing Telemetry Stream..."):
        raw_lc, clean_lc, r_star, teff_star = fetch_data(target_star, selected_quarter)
else:
    raw_lc, clean_lc, r_star, teff_star = None, None, 1.0, 5778.0

if clean_lc is None:
    st.error(f"❌ Data Retrieval Error: Check Target ID '{target_star}'. Try 'Kepler-22' or 'Kepler-452'.")
else:
    # --- A. TRANSIT PHYSICS ---
    periodogram = clean_lc.to_periodogram(method="bls")
    best_period = periodogram.period_at_max_power
    best_t0 = periodogram.transit_time_at_max_power
    transit_depth = periodogram.depth_at_max_power.value

    # --- B. PLANETARY CALCULATIONS ---
    r_planet_jup = np.sqrt(transit_depth) * r_star * 9.731
    period_years = best_period.value / 365.25
    semi_major_axis_au = (period_years ** 2) ** (1/3)
    
    # --- C. HABITABILITY (Temperature) ---
    r_star_au = r_star * 0.00465
    luminosity = (r_star**2) * ((teff_star/5778.0)**4)
    hz_inner_au = np.sqrt(luminosity) * 0.95
    hz_outer_au = np.sqrt(luminosity) * 1.37
    
    eq_temp_k = teff_star * np.sqrt(r_star_au / (2 * semi_major_axis_au)) * ((1 - 0.3)**0.25)
    eq_temp_c = eq_temp_k - 273.15

    # Logic for Status
    if hz_inner_au <= semi_major_axis_au <= hz_outer_au:
        hab_status = "🟩 HABITABLE (Goldilocks Zone)"
        hab_color = "#00ff00"
    elif semi_major_axis_au < hz_inner_au:
        hab_status = "🟥 TOO HOT (Inside HZ)"
        hab_color = "#ff4b4b"
    else:
        hab_status = "🟦 TOO COLD (Outside HZ)"
        hab_color = "#00d4ff"

    # --------------------------------------------------------------------------------
    # 6. RESEARCH DASHBOARD
    # --------------------------------------------------------------------------------
    
    # METRICS ROW
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orbital Period", f"{best_period.value:.4f} d", "Periodic Lock")
    c2.metric("Planet Radius", f"{r_planet_jup:.2f} R_Jup", f"Host: {r_star:.1f} R_Sun")
    c3.metric("Orbital Distance", f"{semi_major_axis_au:.3f} AU", "Semi-Major Axis")
    c4.metric("Surface Temp", f"{eq_temp_c:.0f} °C", hab_status)

    # VISUALIZATION ROW
    folded_lc = clean_lc.fold(period=best_period, epoch_time=best_t0)
    time_delta = (folded_lc.time.value[-1] - folded_lc.time.value[0]) / len(folded_lc.time.value) if len(folded_lc.time.value) > 1 else 0.02
    binned_lc = folded_lc.bin(time_bin_size=(bin_size * time_delta) * u.day)

    tabs = st.tabs(["📊 Phase-Locked Transit", "🪐 Orbital Habitable Zone", "🔭 Raw Telemetry", "💾 Data Export"])

    # --- TAB 1: PHASE PLOT ---
    with tabs[0]:
        st.subheader("Phase-Folded Light Curve Analysis")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=folded_lc.time.value, y=folded_lc.flux.value, mode='markers', name='Raw Flux', marker=dict(color='#00d4ff', size=3, opacity=0.3)))
        fig.add_trace(go.Scatter(x=binned_lc.time.value, y=binned_lc.flux.value, mode='lines+markers', name='Binned Signal', line=dict(color='#ffffff', width=3)))
        fig.update_layout(template="plotly_dark", height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Orbital Phase", yaxis_title="Normalized Flux")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 2: ORBITAL VISUALIZER (THE COOL FEATURE) ---
    with tabs[1]:
        st.subheader("Top-Down Orbital Reconstruction")
        
        # Create Circles for Plot
        theta = np.linspace(0, 2*np.pi, 100)
        
        # HZ Inner
        x_hz_in, y_hz_in = hz_inner_au * np.cos(theta), hz_inner_au * np.sin(theta)
        # HZ Outer
        x_hz_out, y_hz_out = hz_outer_au * np.cos(theta), hz_outer_au * np.sin(theta)
        # Planet Orbit
        x_orb, y_orb = semi_major_axis_au * np.cos(theta), semi_major_axis_au * np.sin(theta)

        fig_orb = go.Figure()

        # 1. Habitable Zone Band (Green)
        fig_orb.add_trace(go.Scatter(x=x_hz_in, y=y_hz_in, mode='lines', line=dict(color='rgba(0,255,0,0.2)', width=1), showlegend=False))
        fig_orb.add_trace(go.Scatter(x=x_hz_out, y=y_hz_out, mode='lines', line=dict(color='rgba(0,255,0,0.2)', width=1), fill='tonexty', fillcolor='rgba(0,255,0,0.1)', name='Habitable Zone'))

        # 2. Planet Orbit
        fig_orb.add_trace(go.Scatter(x=x_orb, y=y_orb, mode='lines', line=dict(color=hab_color, width=2, dash='dash'), name='Planet Orbit'))
        
        # 3. The Star (Center)
        fig_orb.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(color='#ffcc00', size=20, line=dict(color='#ffaa00', width=2)), name='Host Star'))

        # 4. The Planet (Fixed Position for Viz)
        fig_orb.add_trace(go.Scatter(x=[semi_major_axis_au], y=[0], mode='markers', marker=dict(color=hab_color, size=10, line=dict(color='white', width=1)), name='Exoplanet'))

        fig_orb.update_layout(
            template="plotly_dark", 
            height=600, 
            width=600, 
            xaxis=dict(scaleanchor="y", scaleratio=1, title="Distance (AU)", showgrid=False), 
            yaxis=dict(title="Distance (AU)", showgrid=False),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_orb, use_container_width=True)
        st.info(f"Visualizing the Goldilocks Zone (Green Band) based on host star luminosity. Orbit is color-coded by habitability: {hab_status}")

    # --- TAB 3: RAW DATA ---
    with tabs[2]:
        st.subheader("Raw Telemetry Stream")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=clean_lc.time.value, y=clean_lc.flux.value, mode='markers', marker=dict(color='#4c5c75', size=2)))
        fig2.update_layout(template="plotly_dark", height=400, xaxis_title="Time (BJD)", yaxis_title="Flux", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

    # --- TAB 4: EXPORT ---
    with tabs[3]:
        st.subheader("Export Processed Matrix")
        csv = pd.DataFrame({'Phase': folded_lc.time.value, 'Flux': folded_lc.flux.value}).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Analysis CSV", data=csv, file_name=f"{target_star}_analysis.csv", mime="text/csv")
