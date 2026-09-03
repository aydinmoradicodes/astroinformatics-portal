import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURATION & HUD AESTHETIC ---
st.set_page_config(layout="wide", page_title="ExoHunter | Architect", page_icon="🪐")

st.markdown("""
<style>
    /* DEEP SPACE THEME */
    .stApp { background-color: #02040a; background-image: radial-gradient(#111 1px, transparent 0); background-size: 20px 20px; }
    
    /* GLASSMORPHISM CARDS */
    div.stMetric, div.css-1r6slb0 {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(0, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 15px;
    }
    
    /* NEON TYPOGRAPHY */
    h1, h2, h3 { color: #fff; font-family: 'Orbitron', sans-serif; letter-spacing: 2px; text-shadow: 0 0 10px rgba(0, 255, 255, 0.5); }
    .highlight { color: #00e5ff; font-weight: bold; }
    
    /* SLIDER GLOW */
    .stSlider > div > div > div > div { background-color: #00e5ff; box-shadow: 0 0 10px #00e5ff; }
</style>
""", unsafe_allow_html=True)

# --- BACKEND: PHYSICS ENGINE ---

@st.cache_data
def load_and_clean_data():
    """
    Robust Data Loader with Automatic Failover.
    Fetches NASA data or switches to 'Architect Mode' backup if offline.
    """
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_rade,pl_masse,pl_eqt,sy_dist,st_teff,st_rad,disc_year+from+pscomppars+where+pl_rade+is+not+null+and+pl_masse+is+not+null&format=csv"
    try:
        df = pd.read_csv(url)
        df = df.rename(columns={'pl_name': 'Name', 'pl_rade': 'Radius', 'pl_masse': 'Mass', 'pl_eqt': 'Temp_Eq', 'sy_dist': 'Distance'})
        return df, "🟢 NASA DEEP SPACE NETWORK"
    except:
        # The 'Architect' Backup Dataset
        data = {
            'Name': ['Proxima Cen b', 'TRAPPIST-1 e', 'Kepler-442 b', 'Teegarden b', 'K2-18 b', 'LHS 1140 b'],
            'Radius': [1.03, 0.91, 1.34, 1.02, 2.37, 1.63],
            'Mass': [1.07, 0.77, 2.30, 1.05, 8.92, 6.38],
            'Temp_Eq': [234, 251, 233, 260, 265, 230], # Equilibrium Temp (No Atmosphere)
            'Distance': [1.3, 12.1, 342.0, 3.8, 38.0, 14.9]
        }
        return pd.DataFrame(data), "⚠️ ARCHITECT SIMULATION MODE"

def calculate_esi_dynamic(mass, radius, temp):
    """
    Real-time ESI Calculator for the Terraforming Lab.
    Re-evaluates habitability based on user modifications.
    """
    # Earth References
    r_e, rho_e, v_e, t_e = 1.0, 1.0, 1.0, 288.0
    
    # Physics Derivations
    density = mass / (radius ** 3)
    esc_vel = np.sqrt(mass / radius)
    
    # Weights
    w_r, w_rho, w_v, w_t = 0.57, 1.07, 0.70, 5.58
    
    # Similarity Components
    esi_r = (1 - abs((radius - r_e)/(radius + r_e))) ** w_r
    esi_rho = (1 - abs((density - rho_e)/(density + rho_e))) ** w_rho
    esi_v = (1 - abs((esc_vel - v_e)/(esc_vel + v_e))) ** w_v
    esi_t = (1 - abs((temp - t_e)/(temp + t_e))) ** w_t
    
    return (esi_r * esi_rho * esi_v * esi_t) ** (1/4)

def relativity_calculator(dist_pc, velocity_c):
    """
    Solves Time Dilation (Lorentz Factor).
    dist_pc: Distance in Parsecs
    velocity_c: Speed as fraction of Light Speed (0.0 - 0.99)
    """
    if velocity_c >= 1.0: velocity_c = 0.9999 # Limit to prevent infinite mass
    
    dist_km = dist_pc * 3.086e13
    c = 299792.458 # km/s
    
    # 1. Lorentz Factor (Gamma)
    gamma = 1 / np.sqrt(1 - velocity_c**2)
    
    # 2. Travel Time (Earth Frame)
    time_earth_years = (dist_pc * 3.26) / velocity_c
    
    # 3. Travel Time (Ship Frame - Dilated)
    time_ship_years = time_earth_years / gamma
    
    return time_earth_years, time_ship_years, gamma

# --- APP LOGIC ---
df_raw, status = load_and_clean_data()
df_raw = df_raw.dropna().sort_values('Distance')

# SIDEBAR CONTROLLER
st.sidebar.title("🚀 MISSION CONTROL")
st.sidebar.caption(f"LINK STATUS: {status}")

mode = st.sidebar.radio("SELECT MODULE", ["SCANNER", "TERRAFORM LAB", "RELATIVITY ENGINE"])

# --- MODULE 1: THE SCANNER (Discovery) ---
if mode == "SCANNER":
    st.title("🌌 DEEP FIELD SCANNER")
    
    # Dynamic 3D Galaxy Plot
    col1, col2 = st.columns([3, 1])
    with col1:
        # Create a synthetic 3D coordinate system for visualization
        # (Mapping 1D distance to 3D sphere for effect)
        df_viz = df_raw.head(100).copy() # Top 100 closest
        theta = np.linspace(0, 4*np.pi, len(df_viz))
        df_viz['x'] = df_viz['Distance'] * np.cos(theta)
        df_viz['y'] = df_viz['Distance'] * np.sin(theta)
        df_viz['z'] = np.random.uniform(-10, 10, len(df_viz))
        
        fig = px.scatter_3d(
            df_viz, x='x', y='y', z='z',
            color='Temp_Eq', size='Radius',
            hover_name='Name',
            color_continuous_scale='Bluered',
            title='Local Stellar Neighborhood (3D Projection)'
        )
        fig.update_layout(scene=dict(bgcolor='#02040a', xaxis_visible=False, yaxis_visible=False, zaxis_visible=False), paper_bgcolor='#00000000', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Closest Candidates")
        st.dataframe(df_raw[['Name', 'Distance', 'Temp_Eq']].head(10), hide_index=True)

# --- MODULE 2: THE TERRAFORM LAB (Engineering) ---
elif mode == "TERRAFORM LAB":
    st.title("🧬 PLANETARY ENGINEERING LAB")
    st.markdown("Select a candidate and modify atmospheric variables to achieve Habitable Status (ESI > 0.8).")
    
    # 1. Select Planet
    planet_name = st.selectbox("Select Target World", df_raw['Name'].head(20))
    target = df_raw[df_raw['Name'] == planet_name].iloc[0]
    
    # 2. The Simulation Controls
    col_sim1, col_sim2, col_sim3 = st.columns(3)
    
    with col_sim1:
        st.info("BASE STATISTICS")
        st.metric("Radius", f"{target['Radius']:.2f} x Earth")
        st.metric("Base Temp (No Atm)", f"{target['Temp_Eq']:.0f} K")
        
    with col_sim2:
        st.warning("ATMOSPHERIC INJECTION")
        # Greenhouse Effect Simulator
        # Earth's Greenhouse adds ~33K. Venus adds ~500K.
        gh_effect = st.slider("Greenhouse Gas Density (CO2/CH4)", 0, 500, 33, help="Simulate adding an atmosphere. 33K is Earth-like.")
        
        # Albedo Slider (Reflectivity)
        # Higher Albedo = Cooler (Ice). Lower = Warmer (Ocean/Rock).
        albedo_mod = st.slider("Surface Albedo Modifier", 0.5, 1.5, 1.0, help="1.0 = Standard Rock. >1.0 = Ice (Cooling).")
        
    with col_sim3:
        # Physics Calculation
        # Adjusted Temp = (Base / Albedo_Mod) + Greenhouse
        final_temp = (target['Temp_Eq'] / albedo_mod) + gh_effect
        final_esi = calculate_esi_dynamic(target['Mass'], target['Radius'], final_temp)
        
        st.success("SIMULATION RESULTS")
        st.metric("Surface Temp", f"{final_temp:.0f} K", delta=f"{final_temp - 288:.0f} K from Earth")
        
        # ESI Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = final_esi,
            title = {'text': "ESI Score"},
            gauge = {'axis': {'range': [0, 1]}, 'bar': {'color': "#00e5ff"},
                     'steps': [{'range': [0, 0.8], 'color': "#333"}, {'range': [0.8, 1.0], 'color': "rgba(0, 255, 0, 0.3)"}]}
        ))
        fig_gauge.update_layout(height=200, margin=dict(l=20,r=20,t=30,b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
        st.plotly_chart(fig_gauge, use_container_width=True)

# --- MODULE 3: THE RELATIVITY ENGINE (Physics) ---
elif mode == "RELATIVITY ENGINE":
    st.title("⚡ RELATIVISTIC FLIGHT COMPUTER")
    st.markdown("Calculate Time Dilation effects for interstellar travel. Solves the **Twin Paradox** in real-time.")
    
    # Inputs
    c1, c2 = st.columns(2)
    with c1:
        target_p = st.selectbox("Destination System", df_raw['Name'].head(10))
        dist = df_raw[df_raw['Name'] == target_p].iloc[0]['Distance']
        st.metric("Distance", f"{dist:.1f} Parsecs", f"{(dist*3.26):.1f} Light Years")
        
    with c2:
        speed = st.slider("Cruising Velocity (% of Light Speed)", 0.1, 0.999, 0.5, 0.001, format="%.3fc")
    
    # Physics Solver
    t_earth, t_ship, gamma = relativity_calculator(dist, speed)
    
    # Visualization: The Twin Paradox
    st.markdown("---")
    st.subheader("The Einstein Horizon")
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Mission Time (On Ship)", f"{t_ship:.1f} Years", help="How much you age.")
    with m2:
        st.metric("Time Passed (On Earth)", f"{t_earth:.1f} Years", help="How much Aydin ages.")
    with m3:
        st.metric("Time Dilation Factor (γ)", f"{gamma:.2f}x", help="Time moves this many times slower for you.")
        
    # Visual Timeline
    fig_time = go.Figure()
    fig_time.add_trace(go.Bar(
        y=['Aging'], x=[t_ship], orientation='h', name='Astronaut',
        marker=dict(color='#00e5ff')
    ))
    fig_time.add_trace(go.Bar(
        y=['Aging'], x=[t_earth], orientation='h', name='Earth Observer',
        marker=dict(color='#ff0055')
    ))
    fig_time.update_layout(
        title="Relative Aging (Twin Paradox)",
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        xaxis_title="Years Passed"
    )
    st.plotly_chart(fig_time, use_container_width=True)
