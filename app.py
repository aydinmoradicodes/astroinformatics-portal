import streamlit as st
import lightkurve as lk
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import astropy.units as u

# --------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="UBC Astroinformatics Research Portal", 
    page_icon="🛰️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: SpaceX Professional
st.markdown("""
    <style>
    .main { background-color: #0b0d17; }
    h1, h2, h3, h4, .stMarkdown, p, div { font-family: 'Helvetica Neue', sans-serif !important; }
    h1 { color: #ffffff !important; }
    .stMetric { background-color: #15192b; border: 1px solid #2b3044; border-radius: 6px; padding: 15px; }
    div[data-testid="stMetricValue"] { color: #00d4ff !important; }
    [data-testid="stSidebar"] { background-color: #050608; border-right: 1px solid #2b3044; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# 2. HEADER
# --------------------------------------------------------------------------------
st.title("Astroinformatics & Exoplanetary Habitability Pipeline")
st.markdown("""
    **Principal Investigator:** Aydin | **Target Institution:** University of British Columbia (UBC)
    
    *An automated signal processing pipeline utilizing NASA Kepler telemetry to isolate transit signals, 
    simulate real-time orbital dynamics, and estimate planetary habitability potential.*
""")
st.divider()

# --------------------------------------------------------------------------------
# 3. ROBUST SIDEBAR SEARCH
# --------------------------------------------------------------------------------
st.sidebar.header("🔭 Instrument Controls")
target_star = st.sidebar.text_input("Kepler Target ID:", value="Kepler-22")

# --- THE FIX: Aggressive Search Mode ---
if "last_star" not in st.session_state or st.session_state.last_star != target_star:
    st.session_state.last_star = target_star
    with st.spinner("Connecting to NASA MAST Nodes..."):
        try:
            # FIX: Removed 'author' constraint. Now uses 'mission' which is more robust.
            search = lk.search_lightcurve(str(target_star).strip(), mission="Kepler")
            
            # Filter for valid quarters only
            valid_quarters = sorted(list(set([int(q) for q in search.quarter if q is not None and not np.isnan(q)])))
            st.session_state.quarters = valid_quarters
        except Exception as e:
            st.session_state.quarters = []

if "quarters" in st.session_state and st.session_state.quarters:
    selected_quarter = st.sidebar.selectbox("Mission Quarter:", options=st.session_state.quarters, index=0)
else:
    # Fallback message
    st.sidebar.warning(f"Target '{target_star}' not found. Try entering 'KIC 10593626' (Kepler-22 ID) if name fails.")
    selected_quarter = None

bin_size = st.sidebar.slider("Phase Binning Resolution:", 5, 100, 20)
st.sidebar.markdown("---")

# --------------------------------------------------------------------------------
# 4. DATA ENGINE
# --------------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_data(star, quarter):
    if not quarter: return None, None, None, None
    try:
        # Aggressive Download: Mission-based search
        search = lk.search_lightcurve(str(star).strip(), mission="Kepler", quarter=int(quarter))
        if len(search) == 0: return None, None, None, None
        
        # Download the first available flux file to memory
        lc = search[0].download(quality_bitmask='default', download_dir=None)
        if lc is None: return None, None, None, None
        
        # Cleaning Pipeline
        clean_lc = lc.remove_nans().remove_outliers(sigma=5).flatten(window_length=101)
        
        # Metadata Extraction
        r_star = float(lc.meta.get('RADIUS', 1.0) or 1.0)
        teff_star = float(lc.meta.get('TEFF', 5778.0) or 5778.0)
        
        return lc, clean_lc, r_star, teff_star
    except Exception:
        return None, None, None, None

# --------------------------------------------------------------------------------
# 5. EXECUTION CORE
# --------------------------------------------------------------------------------
if selected_quarter:
    with st.spinner(f"Ingesting Telemetry for {target_star} (Q{selected_quarter})..."):
        raw_lc, clean_lc, r_star, teff_star = fetch_data(target_star, selected_quarter)
else:
    raw_lc, clean_lc, r_star, teff_star = None, None, 1.0, 5778.0

if clean_lc is None:
    st.error("Waiting for valid telemetry stream...")
else:
    # --- PHYSICS ENGINE ---
    periodogram = clean_lc.to_periodogram(method="bls")
    best_period = periodogram.period_at_max_power
    best_t0 = periodogram.transit_time_at_max_power
    transit_depth = periodogram.depth_at_max_power.value

    r_planet_jup = np.sqrt(transit_depth) * r_star * 9.731
    period_years = best_period.value / 365.25
    semi_major_axis_au = (period_years ** 2) ** (1/3)
    
    r_star_au = r_star * 0.00465
    eq_temp_k = teff_star * np.sqrt(r_star_au / (2 * semi_major_axis_au)) * ((1 - 0.3)**0.25)
    eq_temp_c = eq_temp_k - 273.15

    if 0 < eq_temp_c < 100: hab_status = "🟩 HABITABLE (Goldilocks Zone)"
    elif eq_temp_c >= 100: hab_status = "🟥 TOO HOT (Inside HZ)"
    else: hab_status = "🟦 TOO COLD (Outside HZ)"

    # --- DASHBOARD ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Orbital Period", f"{best_period.value:.4f} d")
    c2.metric("Planet Radius", f"{r_planet_jup:.2f} R_Jup")
    c3.metric("Orbital Distance", f"{semi_major_axis_au:.3f} AU")
    c4.metric("Surface Temp", f"{eq_temp_c:.0f} °C", hab_status)

    folded_lc = clean_lc.fold(period=best_period, epoch_time=best_t0)
    time_delta = (folded_lc.time.value[-1] - folded_lc.time.value[0]) / len(folded_lc.time.value) if len(folded_lc.time.value) > 1 else 0.02
    binned_lc = folded_lc.bin(time_bin_size=(bin_size * time_delta) * u.day)

    tabs = st.tabs(["📊 Phase-Locked Transit", "🪐 Orbital Habitable Zone", "🔭 Raw Data", "💾 Export"])

    with tabs[0]:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=folded_lc.time.value, y=folded_lc.flux.value, mode='markers', marker=dict(color='#00d4ff', size=3, opacity=0.3), name='Raw Flux'))
        fig.add_trace(go.Scatter(x=binned_lc.time.value, y=binned_lc.flux.value, mode='lines+markers', line=dict(color='#ffffff', width=3), name='Binned Signal'))
        fig.update_layout(template="plotly_dark", height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Orbital Phase", yaxis_title="Normalized Flux")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        # ORBITAL VISUALIZER
        theta = np.linspace(0, 2*np.pi, 100)
        hz_in, hz_out = np.sqrt((r_star**2)*((teff_star/5778)**4))*0.95, np.sqrt((r_star**2)*((teff_star/5778)**4))*1.37
        
        fig_orb = go.Figure()
        fig_orb.add_trace(go.Scatter(x=hz_in*np.cos(theta), y=hz_in*np.sin(theta), mode='lines', line=dict(color='rgba(0,255,0,0.2)'), showlegend=False))
        fig_orb.add_trace(go.Scatter(x=hz_out*np.cos(theta), y=hz_out*np.sin(theta), mode='lines', line=dict(color='rgba(0,255,0,0.2)'), fill='tonexty', fillcolor='rgba(0,255,0,0.1)', name='Habitable Zone'))
        fig_orb.add_trace(go.Scatter(x=semi_major_axis_au*np.cos(theta), y=semi_major_axis_au*np.sin(theta), mode='lines', line=dict(color='#ffffff', dash='dash'), name='Planet Orbit'))
        fig_orb.add_trace(go.Scatter(x=[0], y=[0], mode='markers', marker=dict(color='#ffcc00', size=15), name='Star'))
        fig_orb.update_layout(template="plotly_dark", height=600, width=600, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=True)
        st.plotly_chart(fig_orb, use_container_width=True)

    with tabs[2]:
        st.subheader("Raw Telemetry")
        st.line_chart(clean_lc.flux.value)

    with tabs[3]:
        st.download_button("Download CSV", data=pd.DataFrame({'Time':clean_lc.time.value, 'Flux':clean_lc.flux.value}).to_csv().encode('utf-8'), file_name="data.csv")
