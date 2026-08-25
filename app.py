import streamlit as st
import lightkurve as lk
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import astropy.units as u
from datetime import datetime

# --------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & PROFESSIONAL STYLING
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="UBC Astroinformatics Research Portal", 
    page_icon="🌌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: "SpaceX" Style - Clean, Dark, Data-Dense, No "Game" Fonts
st.markdown("""
    <style>
    /* Main Background: Deep Space Black/Blue (Professional) */
    .main { background-color: #0b0d17; }
    
    /* Typography: Helvetica/Inter (Standard Scientific Fonts) */
    h1, h2, h3, h4, .stMarkdown, p, div { font-family: 'Helvetica Neue', sans-serif !important; }
    
    /* Headers */
    h1 { color: #ffffff !important; font-weight: 700; letter-spacing: -1px; }
    h2, h3 { color: #a0aab5 !important; font-weight: 400; }
    
    /* Metric Cards: Clean, Flat, High-Contrast */
    div[data-testid="stMetricValue"] { font-size: 24px !important; color: #00d4ff !important; }
    div[data-testid="stMetricLabel"] { font-size: 14px !important; color: #8d99ae !important; text-transform: uppercase; }
    .stMetric { background-color: #15192b; border: 1px solid #2b3044; border-radius: 4px; padding: 10px; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #050608; border-right: 1px solid #2b3044; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 2. HEADER & ACADEMIC CREDENTIALS
# --------------------------------------------------------------------------------
st.title("Astroinformatics & Exoplanetary Habitability Pipeline")
st.markdown("""
    **Principal Investigator:** Aydin | **Institution Target:** University of British Columbia (UBC)
    
    *An automated signal processing pipeline utilizing NASA Kepler telemetry to isolate transit signals, 
    simulate real-time orbital dynamics, and estimate planetary habitability potential.*
""")
st.divider()

# --------------------------------------------------------------------------------
# 3. INSTRUMENTATION CONTROLS (SIDEBAR)
# --------------------------------------------------------------------------------
st.sidebar.header("🔭 Instrumentation Controls")
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
# 4. DATA INGESTION ENGINE
# --------------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_data(star, quarter):
    if not quarter: return None, None, None, None
    try:
        search = lk.search_lightcurve(str(star).strip(), author="Kepler", quarter=int(quarter))
        if len(search) == 0: return None, None, None, None
        
        # Download to memory
        lc = search.download(quality_bitmask='default', download_dir=None)
        if lc is None: return None, None, None, None
        
        # Scientific Cleaning: Sigma Clipping & Flattening
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
    st.error(f"❌ Data Retrieval Error: Check Target ID '{target_star}'.")
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
    eq_temp_k = teff_star * np.sqrt(r_star_au / (2 * semi_major_axis_au)) * ((1 - 0.3)**0.25)
    eq_temp_c = eq_temp_k - 273.15

    # Logic for Status
    if 0 < eq_temp_c < 100: hab_status = "🟩 HABITABLE (Liquid Water)"
    elif eq_temp_c >= 100: hab_status = "🟥 TOO HOT (Greenhouse)"
    else: hab_status = "🟦 TOO COLD (Ice World)"

    # --------------------------------------------------------------------------------
    # 6. RESEARCH DASHBOARD
    # --------------------------------------------------------------------------------
    
    # METRICS ROW
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orbital Period", f"{best_period.value:.4f} d", "Locked Signal")
    c2.metric("Planet Radius", f"{r_planet_jup:.2f} R_Jup", f"Host: {r_star:.1f} R_Sun")
    c3.metric("Orbital Distance", f"{semi_major_axis_au:.3f} AU", "Semi-Major Axis")
    c4.metric("Surface Temp", f"{eq_temp_c:.0f} °C", hab_status)

    # VISUALIZATION ROW
    folded_lc = clean_lc.fold(period=best_period, epoch_time=best_t0)
    time_delta = (folded_lc.time.value[-1] - folded_lc.time.value[0]) / len(folded_lc.time.value) if len(folded_lc.time.value) > 1 else 0.02
    binned_lc = folded_lc.bin(time_bin_size=(bin_size * time_delta) * u.day)

    col_left, col_right = st.columns([1.6, 1])

    # --- CHART 1: ANIMATED TRANSIT ---
    with col_left:
        st.subheader("📉 Phase-Locked Transit Analysis")
        # Animation Frames
        n_frames = 8
        chunk = len(folded_lc) // n_frames
        frames = [go.Frame(data=[go.Scatter(x=folded_lc.time.value[:(k+1)*chunk], y=folded_lc.flux.value[:(k+1)*chunk])]) for k in range(n_frames)]

        fig_anim = go.Figure(
            data=[
                go.Scatter(x=folded_lc.time.value[:chunk], y=folded_lc.flux.value[:chunk], mode='markers', marker=dict(color='#00d4ff', size=3, opacity=0.4), name='Flux Data'),
                go.Scatter(x=binned_lc.time.value, y=binned_lc.flux.value, mode='lines+markers', line=dict(color='#ffffff', width=2), marker=dict(size=5, color='#ffffff'), name='Binned Model')
            ],
            layout=go.Layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                xaxis=dict(title="Orbital Phase (Days)", showgrid=True, gridcolor='#2b3044'),
                yaxis=dict(title="Relative Flux", showgrid=True, gridcolor='#2b3044'),
                margin=dict(l=0, r=0, t=0, b=0),
                updatemenus=[dict(type="buttons", showactive=False, buttons=[dict(label="▶ Simulate Scan", method="animate", args=[None, dict(frame=dict(duration=120))])])]
            ),
            frames=frames
        )
        st.plotly_chart(fig_anim, use_container_width=True)

    # --- CHART 2: REAL-TIME SOLAR SYSTEM MAP ---
    with col_right:
        st.subheader("🪐 Real-Time Orbital Geometry")
        
        # Real-Time Position Math
        current_time = 2454833.0 + (datetime.utcnow() - datetime(2009, 1, 1)).total_seconds() / 86400.0
        phase = ((current_time - best_t0.value) % best_period.value) / best_period.value * 2 * np.pi
        px, py = semi_major_axis_au * np.cos(phase), semi_major_axis_au * np.sin(phase)
        
        # Zones
        lum = (teff_star/5778)**4 * (r_star)**2
        hz_in, hz_out = 0.95 * np.sqrt(lum), 1.37 * np.sqrt(lum)
        
        fig_map = go.Figure()
        
        # Star
        fig_map.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(size=30, color='#ffcc00'), name='Star'))
        
        # HZ Ring (Green)
        theta = np.linspace(0, 2*np.pi, 100)
        fig_map.add_trace(go.Scatter(x=hz_out*np.cos(theta), y=hz_out*np.sin(theta), mode='lines', line=dict(width=0), fill='toself', fillcolor='rgba(0,255,0,0.1)', name='Habitable Zone'))
        fig_map.add_trace(go.Scatter(x=hz_in*np.cos(theta), y=hz_in*np.sin(theta), mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(0,255,0,0.2)', showlegend=False))
        
        # Orbit & Planet
        fig_map.add_trace(go.Scatter(x=semi_major_axis_au*np.cos(theta), y=semi_major_axis_au*np.sin(theta), mode='lines', line=dict(color='#444', dash='dash'), showlegend=False))
        fig_map.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(size=10, color='#00d4ff', line=dict(width=2, color='white')), name='Planet'))
        
        lim = max(hz_out, semi_major_axis_au) * 1.2
        fig_map.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(range=[-lim, lim], visible=False),
            yaxis=dict(range=[-lim, lim], visible=False, scaleanchor="x", scaleratio=1),
            height=400, margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(orientation="h", y=0, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # --------------------------------------------------------------------------------
    # 7. DATA EXPORT
    # --------------------------------------------------------------------------------
    with st.expander("📂 Export Processed Telemetry"):
        st.dataframe(pd.DataFrame({'Time_BJD': clean_lc.time.value, 'Flux_Norm': clean_lc.flux.value}).head(100), use_container_width=True)
        st.download_button("Download Full CSV", clean_lc.to_pandas().to_csv().encode('utf-8'), "telemetry.csv", "text/csv")
