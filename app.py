import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="ExoHunter | Deep Space Analysis", page_icon="🔭")

# Custom "Deep Space" CSS
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    h1, h2, h3 { color: #00e5ff; font-family: 'Helvetica Neue', sans-serif; font-weight: 300; }
    .metric-card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid #333; }
    .highlight { color: #00e5ff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- BACKEND: DATA & PHYSICS ENGINE ---

@st.cache_data
def load_data():
    """
    Fetches the NASA Exoplanet Archive.
    Includes a 'Fail-Safe' backup dataset to ensure 100% uptime for demos.
    """
    # 1. LIVE DATA: Try to fetch from Caltech/NASA
    nasa_url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_rade,pl_masse,pl_eqt,sy_dist,st_teff,st_rad,disc_year+from+pscomppars+where+pl_rade+is+not+null+and+pl_masse+is+not+null&format=csv"
    
    try:
        df = pd.read_csv(nasa_url)
        # Rename columns for readability
        df = df.rename(columns={
            'pl_name': 'Name',
            'pl_rade': 'Radius (Earth)',
            'pl_masse': 'Mass (Earth)',
            'pl_eqt': 'Temp (K)',
            'sy_dist': 'Distance (pc)',
            'st_teff': 'Star Temp (K)',
            'disc_year': 'Discovery Year'
        })
        return df, "🟢 NASA LIVE FEED"
    except:
        # 2. BACKUP DATA: If NASA API fails, use this hardcoded 'Greatest Hits' list
        # This guarantees the app NEVER shows an error screen.
        data = {
            'Name': ['Proxima Cen b', 'TRAPPIST-1 e', 'Kepler-442 b', 'Teegarden b', 'K2-18 b', 'Ross 128 b'],
            'Radius (Earth)': [1.03, 0.91, 1.34, 1.02, 2.37, 1.35],
            'Mass (Earth)': [1.07, 0.77, 2.30, 1.05, 8.92, 1.40],
            'Temp (K)': [234, 251, 233, 260, 265, 280],
            'Distance (pc)': [1.3, 12.1, 342.0, 3.8, 38.0, 3.37],
            'Star Temp (K)': [3042, 2566, 4402, 2900, 3500, 3192],
            'Discovery Year': [2016, 2017, 2015, 2019, 2015, 2017]
        }
        return pd.DataFrame(data), "jg-orange[OFFLINE MODE]"

def calculate_esi(df):
    """
    The 'UBC Physics' Flex:
    Calculates the Earth Similarity Index (ESI) using Schulze-Makuch's formula.
    ESI = 1.0 is Earth. 0.8+ is 'Earth-Like'.
    """
    # Earth Reference Values
    r_earth = 1.0
    rho_earth = 1.0 # Density (normalized)
    v_esc_earth = 1.0 # Escape Velocity (normalized)
    t_earth = 288.0 # Surface Temp (Kelvin)

    # Weights for the formula (Temperature is most critical)
    w_r = 0.57
    w_rho = 1.07
    w_v = 0.70
    w_t = 5.58
    
    # 1. Estimate Density (ρ) if Mass & Radius are known
    # ρ ~ Mass / Radius^3
    df['Density'] = df['Mass (Earth)'] / (df['Radius (Earth)'] ** 3)
    
    # 2. Estimate Escape Velocity (v)
    # v ~ sqrt(Mass / Radius)
    df['Esc Vel'] = np.sqrt(df['Mass (Earth)'] / df['Radius (Earth)'])
    
    # 3. The ESI Formula
    # We compare Radius, Density, Esc Vel, and Temperature to Earth
    df['ESI_Radius'] = (1 - np.abs((df['Radius (Earth)'] - r_earth) / (df['Radius (Earth)'] + r_earth))) ** w_r
    df['ESI_Density'] = (1 - np.abs((df['Density'] - rho_earth) / (df['Density'] + rho_earth))) ** w_rho
    df['ESI_EscVel'] = (1 - np.abs((df['Esc Vel'] - v_esc_earth) / (df['Esc Vel'] + v_esc_earth))) ** w_v
    df['ESI_Temp'] = (1 - np.abs((df['Temp (K)'] - t_earth) / (df['Temp (K)'] + t_earth))) ** w_t
    
    # Geometric Mean of the components
    df['ESI'] = (df['ESI_Radius'] * df['ESI_Density'] * df['ESI_EscVel'] * df['ESI_Temp']) ** (1/4)
    
    return df

# --- FRONTEND: THE DASHBOARD ---

# 1. Load & Process Data
raw_df, status = load_data()
df = calculate_esi(raw_df.dropna()) # Remove incomplete data rows

# Sidebar: Research Controls
st.sidebar.title("🔍 OBSERVATORY CONTROLS")
st.sidebar.markdown(f"**DATA SOURCE:** {status}")

# Filters
st.sidebar.subheader("Habitability Filters")
min_esi = st.sidebar.slider("Minimum ESI (Earth Similarity)", 0.0, 1.0, 0.7, 0.05)
max_temp = st.sidebar.slider("Max Equilibrium Temp (K)", 200, 500, 350)
max_dist = st.sidebar.slider("Max Distance (Parsecs)", 0, 1000, 100)

# Apply Filters
filtered_df = df[
    (df['ESI'] >= min_esi) & 
    (df['Temp (K)'] <= max_temp) & 
    (df['Distance (pc)'] <= max_dist)
]

# MAIN PANEL
c1, c2 = st.columns([2, 1])
with c1:
    st.title("EXO-HUNTER")
    st.caption("Computational Astrobiology & Candidate Selection Tool")
with c2:
    st.metric("CANDIDATES FOUND", len(filtered_df), f"Total Database: {len(df)}")

# VISUALIZATION 1: The "Goldilocks Zone" Scatter
st.subheader("The Goldilocks Zone Analysis")
fig_scatter = px.scatter(
    filtered_df,
    x="Temp (K)",
    y="Radius (Earth)",
    color="ESI",
    size="Mass (Earth)",
    hover_name="Name",
    color_continuous_scale="Viridis",
    range_x=[400, 150], # Inverted X axis (Hot left, Cold right)
    range_y=[0.5, 3.0],
    title="Planetary Radius vs. Equilibrium Temperature"
)
# Add a rectangle for the "Habitable Zone"
fig_scatter.add_shape(type="rect",
    x0=200, y0=0.8, x1=320, y1=1.5,
    line=dict(color="Green", width=2),
    fillcolor="rgba(0,255,0,0.1)",
)
fig_scatter.update_layout(plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font_color="white")
st.plotly_chart(fig_scatter, use_container_width=True)

# VISUALIZATION 2: 3D Galaxy Map
st.subheader("3D Galactic Neighborhood")
col_map, col_details = st.columns([2, 1])

with col_map:
    # 3D Plot of where these planets are relative to Earth
    # (Simplified: Using Distance/Random Angle as we lack full RA/DEC in this simple CSV view)
    theta = np.random.uniform(0, 2*np.pi, len(filtered_df))
    phi = np.random.uniform(0, np.pi, len(filtered_df))
    x = filtered_df['Distance (pc)'] * np.sin(phi) * np.cos(theta)
    y = filtered_df['Distance (pc)'] * np.sin(phi) * np.sin(theta)
    z = filtered_df['Distance (pc)'] * np.cos(phi)
    
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(
            size=5,
            color=filtered_df['ESI'],
            colorscale='Viridis',
            opacity=0.8
        ),
        text=filtered_df['Name'],
        hoverinfo='text'
    )])
    
    fig_3d.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode='markers',
        marker=dict(size=10, color='red'),
        name='Earth'
    ))
    
    fig_3d.update_layout(
        scene = dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor='#000000'
        ),
        margin=dict(r=0, l=0, b=0, t=0),
        paper_bgcolor="#000000",
        height=400
    )
    st.plotly_chart(fig_3d, use_container_width=True)

with col_details:
    st.markdown("### TOP CANDIDATE")
    if not filtered_df.empty:
        best_planet = filtered_df.loc[filtered_df['ESI'].idxmax()]
        st.info(f"**NAME:** {best_planet['Name']}")
        st.write(f"**ESI SCORE:** {best_planet['ESI']:.3f}")
        st.write(f"**RADIUS:** {best_planet['Radius (Earth)']:.2f} x Earth")
        st.write(f"**TEMP:** {best_planet['Temp (K)']:.0f} K")
        st.write(f"**DIST:** {best_planet['Distance (pc)']:.1f} pc")
        
        # Determine Verdict
        if best_planet['ESI'] > 0.85:
            st.success("VERDICT: High Probability of Habitability")
        else:
            st.warning("VERDICT: Potential Extremophile Environment")
    else:
        st.error("No planets match current filters.")
