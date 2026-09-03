import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. ARCHITECT GRADE UI CONFIGURATION ---
st.set_page_config(layout="wide", page_title="ExoHunter | Omni-Architect", page_icon="🔭")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;600&display=swap');

    /* COSMIC VOID BACKGROUND */
    .stApp {
        background-color: #030508;
        background-image: 
            radial-gradient(circle at 50% 50%, rgba(0, 242, 255, 0.05) 0%, transparent 50%),
            radial-gradient(white, rgba(255,255,255,.1) 1px, transparent 1px);
        background-size: 100% 100%, 40px 40px;
    }

    /* GLASSMORPHISM DASHBOARD */
    div.stMetric, div.css-1r6slb0 {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.2);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(8px);
        border-radius: 12px;
        color: #e0f2fe;
    }

    /* HOLOGRAPHIC TYPOGRAPHY */
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #38bdf8 !important; letter-spacing: 2px; }
    p, label, span, div { font-family: 'Rajdhani', sans-serif !important; color: #cbd5e1; font-size: 17px; }

    /* SLIDER & INPUT GLOW */
    .stSlider > div > div > div > div { background-color: #38bdf8; box-shadow: 0 0 10px #38bdf8; }
    
    /* CUSTOM ALERTS */
    .success-box { border-left: 5px solid #00ff41; background: rgba(0, 255, 65, 0.1); padding: 10px; }
    .fail-box { border-left: 5px solid #ff0055; background: rgba(255, 0, 85, 0.1); padding: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. ADVANCED PHYSICS ENGINE ---

@st.cache_data
def load_telemetry():
    """Robust Data Loader with Range Filtering"""
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_rade,pl_masse,pl_eqt,sy_dist,st_teff,st_rad,disc_year+from+pscomppars+where+pl_rade+is+not+null+and+pl_masse+is+not+null&format=csv"
    try:
        df = pd.read_csv(url)
        df = df.rename(columns={'pl_name': 'Name', 'pl_rade': 'Radius', 'pl_masse': 'Mass', 'pl_eqt': 'Temp', 'sy_dist': 'Distance'})
        # Filter for "interesting" planets (Not gas giants, not frozen rocks)
        # We want planets between 0.5 and 2.5 Earth Radii to ensure they are rocky
        df = df[(df['Radius'] > 0.5) & (df['Radius'] < 2.5)]
        return df.dropna().sort_values('Distance'), "ONLINE (NASA DEEP SPACE NETWORK)"
    except:
        # Architect Backup Set (Includes Cold, Hot, and Warm worlds for testing)
        data = {
            'Name': ['Proxima Cen b', 'TRAPPIST-1 e', 'Kepler-442 b', 'Teegarden b', 'Ross 128 b', 'Kepler-186 f'],
            'Radius': [1.03, 0.91, 1.34, 1.02, 1.35, 1.17],
            'Mass': [1.07, 0.77, 2.30, 1.05, 1.40, 1.71],
            'Temp': [234, 251, 260, 290, 301, 188], # Mix of temps
            'Distance': [1.3, 12.1, 342.0, 3.8, 3.37, 178.5]
        }
        return pd.DataFrame(data), "OFFLINE (SIMULATION PROTOCOL)"

def calculate_thermodynamics(base_temp, greenhouse, albedo, sunshade):
    """
    OMNI ENGINE: Calculates new surface temp based on Engineering Inputs.
    New Feature: 'Sunshade' (Cooling)
    Formula: T_new = T_star * ((1 - Albedo) * (1 - Sunshade))^0.25 + Greenhouse
    """
    # Simplifying the Stefan-Boltzmann adaptation for gameplay balance
    # 1. Apply Sunshade (Reduces incoming flux)
    temp_after_shade = base_temp * ((1 - sunshade) ** 0.25)
    
    # 2. Apply Albedo (Reflectivity)
    # Base temp assumes generic albedo (0.3). We adjust relative to that.
    temp_after_albedo = temp_after_shade * ((1 / albedo) ** 0.1) 
    
    # 3. Apply Greenhouse (Traps heat)
    final_temp = temp_after_albedo + (greenhouse * 0.5)
    
    return final_temp

def get_planet_color(temp, pressure, vegetation_type):
    """Generates procedural texture based on Phase State and Biology"""
    if temp > 400: return [[0, 'black'], [0.5, 'red'], [1, 'orange']], "MAGMA"
    if temp < 200: return 'Blues', "ICE SHELL"
    if pressure < 0.1: return 'Greys', "BARREN ROCK"
    
    # Habitable Colors based on Star Type
    if 270 < temp < 320:
        if vegetation_type == "Red Dwarf (Black Flora)":
            return [[0, 'navy'], [0.4, 'purple'], [0.6, 'black'], [1, 'white']], "EXOTIC BIO"
        else:
            return [[0, 'navy'], [0.4, 'blue'], [0.5, 'forestgreen'], [0.6, 'green'], [1, 'white']], "TERRAN BIO"
            
    return 'YlOrBr', "DESERT"

# --- 3. UI LAYOUT ---

df, status = load_telemetry()

# SIDEBAR
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg", width=140)
    st.title("EXO-HUNTER")
    st.markdown("**OMNI-ARCHITECT v7.2**")
    st.caption(f"DATA LINK: {status}")
    
    mode = st.radio("MODULE SELECT", ["🧬 PLANETARY ENGINEERING", "🚀 RELATIVITY SOLVER", "🔭 GALAXY ARRAY"])
    
    st.markdown("---")
    if mode == "🧬 PLANETARY ENGINEERING":
        st.write("**TARGET DESIGNATION:**")
        # Ensure only valid options
        selected_planet = st.selectbox("Select World", df['Name'].head(20).tolist())
        p_data = df[df['Name'] == selected_planet].iloc

# --- MODULE 1: PLANETARY ENGINEERING (THE UPGRADE) ---
if mode == "🧬 PLANETARY ENGINEERING":
    col_controls, col_viz = st.columns([1, 1.5])
    
    with col_controls:
        st.subheader("/// TERRAFORMING CONSOLE")
        
        # 1. The Cooling Mechanism (NEW)
        st.markdown("**1. ORBITAL MEGA-STRUCTURES (COOLING)**")
        sunshade = st.slider("Solar Shade Array Coverage", 0.0, 0.9, 0.0, help="Deploys Lagrange Point mirrors to block starlight. COOLS the planet.")
        
        # 2. The Heating Mechanism
        st.markdown("**2. ATMOSPHERIC INJECTION (HEATING)**")
        gh_gas = st.slider("Greenhouse Gas Density (ppm)", 0, 800, 30, help="Injects CO2/CH4 to trap heat.")
        
        # 3. Surface Modification
        st.markdown("**3. HYDRO-GEO ENGINEERING**")
        albedo = st.slider("Surface Albedo", 0.1, 1.0, 0.3, help="0.1 = Dark Rock (Hot), 1.0 = Ice Sheet (Cold)")
        
        # Physics Calc
        base_temp = p_data['Temp']
        final_temp = calculate_thermodynamics(base_temp, gh_gas, albedo, sunshade)
        
        # 4. Phase Calculation (Pressure)
        pressure = st.slider("Atmospheric Pressure (atm)", 0.0, 2.0, 1.0)
        
        # RESULTS HUD
        st.markdown("---")
        m1, m2 = st.columns(2)
        m1.metric("Surface Temp", f"{final_temp:.0f} K", delta=f"{final_temp - 288:.0f} K from Earth")
        
        # ESI Logic
        esi = 1.0 - (abs(final_temp - 288) / 288) - (abs(pressure - 1.0)/4)
        if esi < 0: esi = 0
        m2.metric("Habitability Index (ESI)", f"{esi:.2f}", delta="Target: > 0.8")

        # STATUS CHECK
        if 273 < final_temp < 323 and pressure > 0.5:
            st.markdown('<div class="success-box">✅ STATUS: LIQUID WATER STABLE</div>', unsafe_allow_html=True)
            bio_status = "ACTIVE"
        elif final_temp > 373:
             st.markdown('<div class="fail-box">⚠️ STATUS: BOILING / VAPORIZED</div>', unsafe_allow_html=True)
             bio_status = "DEAD"
        else:
             st.markdown('<div class="fail-box">❄️ STATUS: GLOBAL GLACIATION</div>', unsafe_allow_html=True)
             bio_status = "DORMANT"

    with col_viz:
        # THE VISUAL UPGRADE: PHASE DIAGRAM & 3D PLANET
        st.subheader("/// REAL-TIME TELEMETRY")
        
        tab1, tab2 = st.tabs(["🪐 ORBITAL VIEW", "📈 PHASE DIAGRAM"])
        
        with tab1:
            # 3D Render
            colors, biome = get_planet_color(final_temp, pressure, "Terran")
            
            # Procedural Sphere
            phi, theta = np.meshgrid(np.linspace(0, 2*np.pi, 100), np.linspace(0, np.pi, 100))
            x = np.sin(theta) * np.cos(phi)
            y = np.sin(theta) * np.sin(phi)
            z = np.cos(theta)
            
            # Surface Noise
            surf = np.sin(phi*3)*np.cos(theta*3) + np.random.rand(100,100)*0.2
            
            fig_3d = go.Figure(go.Surface(
                x=x, y=y, z=z, surfacecolor=surf, colorscale=colors,
                lighting=dict(ambient=0.4, diffuse=0.9, specular=0.2),
                lightposition=dict(x=100, y=100, z=100)
            ))
            fig_3d.update_layout(
                title=f"VISUAL FEED: {biome}",
                scene=dict(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False, bgcolor='rgba(0,0,0,0)'),
                paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,b=0,t=30), height=400
            )
            st.plotly_chart(fig_3d, use_container_width=True)
            
        with tab2:
            # PHASE DIAGRAM (The Math Flex)
            # Create the Phase Lines
            t_range = np.linspace(150, 500, 100)
            # Simplified Clausius-Clapeyron curves for water
            p_sublimation = 0.006 * np.exp(24 * (1 - 273/t_range)) # Ice -> Vapor
            p_boiling = 1.0 * np.exp(13 * (1 - 373/t_range))      # Water -> Vapor
            
            fig_phase = go.Figure()
            
            # 1. The Zones
            fig_phase.add_trace(go.Scatter(x=t_range, y=p_boiling, mode='lines', name='Boiling Point', line=dict(color='red')))
            fig_phase.add_shape(type="rect", x0=273, y0=0.006, x1=373, y1=20, fillcolor="rgba(0, 255, 65, 0.1)", line=dict(width=0), name="Liquid Water")
            
            # 2. The Current Planet Marker
            fig_phase.add_trace(go.Scatter(
                x=[final_temp], y=[pressure],
                mode='markers+text', text=["CURRENT STATE"], textposition="top center",
                marker=dict(size=15, color='#00f2ff', symbol='diamond', line=dict(color='white', width=2)),
                name='Planet State'
            ))
            
            fig_phase.update_layout(
                title="H2O PHASE DIAGRAM",
                xaxis_title="Temperature (K)", yaxis_title="Pressure (atm)",
                yaxis_type="log", yaxis_range=[-3, 1], xaxis_range=[200, 500],
                plot_bgcolor='rgba(0,0,0,0.5)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white")
            )
            st.plotly_chart(fig_phase, use_container_width=True)

# --- MODULE 2: RELATIVITY SOLVER (POLISHED) ---
elif mode == "🚀 RELATIVITY SOLVER":
    st.title("INTERSTELLAR FLIGHT COMPUTER")
    
    c1, c2 = st.columns(2)
    with c1:
        target = st.selectbox("Destination System", df['Name'].head(10))
        dist = df.loc[df['Name'] == target, 'Distance'].values
        st.metric("Linear Distance", f"{dist:.1f} Parsecs")
        
    with c2:
        velocity = st.slider("Impulse Velocity (% c)", 0.1, 0.9999, 0.8, 0.0001, format="%.4f")
    
    # Physics
    gamma = 1 / np.sqrt(1 - velocity**2)
    t_ship = (dist * 3.26) / velocity / gamma
    t_earth = (dist * 3.26) / velocity
    
    st.markdown("---")
    
    # VISUAL: Cockpit Dashboard
    g1, g2, g3 = st.columns(3)
    
    with g1:
        fig_g = go.Figure(go.Indicator(
            mode = "gauge+number", value = gamma, title = {'text': "Lorentz Factor"},
            gauge = {'axis': {'range':}, 'bar': {'color': "#38bdf8"}}
        ))
        fig_g.update_layout(height=200, margin=dict(l=10,r=10,t=30,b=10), paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig_g, use_container_width=True)
    
    with g2:
        st.metric("Ship Clock (You)", f"{t_ship:.1f} Yrs", help="Subjective Time")
    with g3:
        st.metric("Earth Clock (Mission Control)", f"{t_earth:.1f} Yrs", help="Observer Time")
    
    st.info(f"**ANALYSIS:** Due to Time Dilation, you will age {t_earth - t_ship:.1f} years LESS than your colleagues on Earth.")

# --- MODULE 3: GALAXY ARRAY ---
elif mode == "🔭 GALAXY ARRAY":
    st.title("DEEP FIELD SENSOR ARRAY")
    
    # 4D Bubble Chart (X, Y, Z, Size, Color)
    fig = px.scatter_3d(
        df.head(150), x='Distance', y='Temp', z='Radius',
        color='Mass', size='Radius', hover_name='Name',
        color_continuous_scale='Portland', opacity=0.8,
        title="Stellar Neighborhood: Mass vs. Habitability"
    )
    fig.update_layout(
        scene=dict(bgcolor='rgba(0,0,0,0)', xaxis=dict(gridcolor='#1e293b'), yaxis=dict(gridcolor='#1e293b'), zaxis=dict(gridcolor='#1e293b')),
        paper_bgcolor='rgba(0,0,0,0)', font_color='#38bdf8', height=650,
        margin=dict(l=0,r=0,b=0,t=40)
    )
    st.plotly_chart(fig, use_container_width=True)
