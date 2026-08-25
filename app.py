import streamlit as st
import lightkurve as lk
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import astropy.units as u

# Configure the Streamlit Page for an enterprise research appearance
st.set_page_config(
    page_title="Astroinformatics Research Portal", 
    page_icon="🌌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS injection for elite Midnight Academic styling
st.markdown("""
    <style>
    .main { background-color: #05070f; }
    h1 { color: #00bbf9 !important; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    h2, h3 { color: #9b5de5 !important; }
    .stMetric { background-color: #0e1222; padding: 15px; border-radius: 10px; border: 1px solid #1e295d; }
    div[data-testid="stMetricDelta"] > div { color: #f15bb5 !important; }
    </style>
""", unsafe_allow_html=True)

# Academic-Grade Header
st.title("Astroinformatics & Exoplanetary Transit Pipeline")
st.markdown("""
    **Research Engineer:** Aydin | **Target Institution:** University of British Columbia (UBC)
    
    *An automated computational signal processing pipeline utilizing live telemetry from NASA's Kepler Space Telescope via the MAST Archive to isolate transits and extract physical exoplanetary characteristics.*
""")
st.divider()

# Mission Control Sidebar
st.sidebar.header("Control Panel")
target_star = st.sidebar.text_input("Kepler Target Star:", value="Kepler-8")

# Initialize session state for storing quarters to prevent redundant API queries
if "last_star" not in st.session_state or st.session_state.last_star != target_star:
    st.session_state.last_star = target_star
    with st.spinner("Querying available NASA observation windows..."):
        try:
            # Force explicit string conversion for the query target
            search_result = lk.search_lightcurve(str(target_star).strip(), author="Kepler")
            available_quarters = sorted([int(q) for q in search_result.quarter if q is not None and not np.isnan(q)])
            st.session_state.available_quarters = available_quarters
        except Exception:
            st.session_state.available_quarters = []

# Dynamically populate quarter selector based on what NASA actually has on file
if "available_quarters" in st.session_state and st.session_state.available_quarters:
    selected_quarter = st.sidebar.selectbox(
        "Available Kepler Mission Quarters:", 
        options=st.session_state.available_quarters,
        index=0
    )
else:
    st.sidebar.warning("Star search pending or target not found.")
    selected_quarter = None

bin_size = st.sidebar.slider("Phase Binning Vector Size:", min_value=5, max_value=100, value=25, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown("### Calculated Physical Properties")

# High-Compatibility NASA Data Fetching & Signal Cleaning Engine
@st.cache_data(show_spinner="Streaming Live Telemetry from NASA MAST...", ttl=3600)
def fetch_stellar_data(star, quarter):
    if quarter is None:
        return None, None, None
    try:
        # Perform target lookup with explicit constraints to resolve container routing blocks
        search_result = lk.search_lightcurve(str(star).strip(), author="Kepler", quarter=int(quarter))
        if len(search_result) == 0:
            return None, None, None
        
        # Pull data arrays directly into memory, disabling disk caching to circumvent cloud write permission limits
        raw_lc = search_result[0].download(quality_bitmask='default', download_dir=None)
        if raw_lc is None:
            return None, None, None
            
        # Clean Signal: Strip missing steps, clear instruments shocks, and flatten baseline variance
        clean_lc = raw_lc.remove_nans().remove_outliers(sigma=5).flatten(window_length=101)
        
        # Pull authentic catalog stellar radius metadata
        try:
            r_star = raw_lc.meta.get('RADIUS', 1.0)
            if r_star is None or np.isnan(float(r_star)):
                r_star = 1.0
        except Exception:
            r_star = 1.0
            
        return raw_lc, clean_lc, float(r_star)
    except Exception:
        return None, None, None

# Execute Pipeline
if selected_quarter:
    raw_lc, clean_lc, r_star = fetch_stellar_data(target_star, selected_quarter)
else:
    raw_lc, clean_lc, r_star = None, None, None

if clean_lc is None:
    st.error(f"Pipeline Failure: Unable to fetch archival records for '{target_star}'. Verify object syntax (e.g., 'Kepler-10', 'Kepler-8').")
else:
    # Periodogram Frequency Analysis via Box Least Squares (BLS)
    with st.spinner("Executing Box Least Squares (BLS) Period Search..."):
        periodogram = clean_lc.to_periodogram(method="bls")
        best_period = periodogram.period_at_max_power
        best_t0 = periodogram.transit_time_at_max_power
        transit_depth = periodogram.depth_at_max_power.value

    # Physical Boundary Math
    r_ratio = np.sqrt(transit_depth)
    actual_radius_jup = r_ratio * r_star * 9.731 

    # Metrics Layout in Sidebar
    st.sidebar.metric(label=r"Orbital Period ($P$)", value=f"{best_period.value:.5f} Days")
    st.sidebar.metric(label=r"Stellar Flux Dimming ($\Delta F$)", value=f"{transit_depth*100:.4f}%")
    st.sidebar.metric(label=r"Calculated Physical Radius ($R_p$)", value=f"~{actual_radius_jup:.2f} x R_Jup", delta=f"Host Star: {r_star:.2f} R_Sun")

    # Data Dimensionality Folding & Safe Astropy Binning 
    folded_lc = clean_lc.fold(period=best_period, epoch_time=best_t0)
    
    # Safely isolate time vector gaps using explicit array delta evaluation
    time_delta = (folded_lc.time.value[-1] - folded_lc.time.value[0]) / len(folded_lc.time.value) if len(folded_lc.time.value) > 1 else 0.02
    binned_lc = folded_lc.bin(time_bin_size=(bin_size * time_delta) * u.day)

    # Scientific Interactive Visualizations (Plotly Engine Layout)
    tabs = st.tabs(["Full Continuous Timeline", "Phase-Folded Transit Profile", "Export Subsystem"])

    with tabs[0]:
        st.subheader("Continuous Telemetry Time-Series")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=clean_lc.time.value,
            y=clean_lc.flux.value,
            mode='markers',
            marker=dict(size=2, color='#9b5de5', opacity=0.6),
            name='Stellar Flux'
        ))
        fig1.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Time (Barycentric Julian Date)",
            yaxis_title="Normalized Flux",
            margin=dict(l=40, r=40, t=20, b=40),
            height=450
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.caption("Raw time-series data capturing continuous stellar observations over a full mission quarter.")

    with tabs[1]:
        st.subheader("Phase-Folded Exoplanetary Silhouette")
        fig2 = go.Figure()
        
        # Raw folded data
        fig2.add_trace(go.Scatter(
            x=folded_lc.time.value,
            y=folded_lc.flux.value,
            mode='markers',
            marker=dict(size=3, color='#00bbf9', opacity=0.25),
            name='Individual Observations'
        ))
        
        # Statistically binned signal
        fig2.add_trace(go.Scatter(
            x=binned_lc.time.value,
            y=binned_lc.flux.value,
            mode='markers+lines',
            marker=dict(size=8, color='#f15bb5', symbol='circle'),
            line=dict(width=2, color='#f15bb5'),
            name='Statistical Phase-Binning'
        ))
        
        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Phase (Days from Mid-Transit)",
            yaxis_title="Relative Flux Deficit",
            margin=dict(l=40, r=40, t=20, b=40),
            height=450
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Phase folding maps hundreds of distinct observations into a unified orbital footprint to clarify the signal-to-noise ratio.")

    with tabs[2]:
        st.subheader("Research Data Export Architecture")
        
        # Generate DataFrame safe for ingestion into data analytics pipelines
        export_df = pd.DataFrame({
            'Phase_Days': folded_lc.time.value,
            'Normalized_Flux': folded_lc.flux.value
        }).dropna()
        
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        
        st.info("Admissions review option: Download the processed lightcurve matrix directly as a structured CSV for validation in NumPy/Pandas pipelines.")
        st.download_button(
            label="Download Phase-Folded Matrix (CSV)",
            data=csv_data,
            file_name=f"{target_star}_folded_telemetry.csv",
            mime="text/csv",
            use_container_width=True
        )
