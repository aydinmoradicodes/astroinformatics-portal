import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. THE CINEMATIC CONFIGURATION ---
st.set_page_config(layout="wide", page_title="ExoHunter | Genesis", page_icon="🪐")

# Injecting "Orbitron" Font & Deep Space Background
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500&display=swap');

    /* BACKGROUND: Deep Space Starfield */
    .stApp {
        background-color: #000000;
        background-image: 
            radial-gradient(white, rgba(255,255,255,.2) 2px, transparent 3px),
            radial-gradient(white, rgba(255,255,255,.15) 1px, transparent 2px),
            radial-gradient(white, rgba(255,255,255,.1) 2px, transparent 3px);
        background-size: 550px 550px, 350px 350px, 250px 250px;
        background-position: 0 0, 40px 60px, 130px 270px;
    }

    /* HUD TYPOGRAPHY */
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; text-shadow: 0px 0px 10px rgba(0, 242, 255, 0.6); }
    p, div, label { font-family: 'Rajdhani', sans-serif !important; font-size: 18px; color: #e0e0e0; }

    /* GLASSMORPHISM PANELS */
    div.stMetric, div.css-1r6slb0 {
        background: rgba(10, 20, 30, 0.7);
        border: 1px solid rgba(0, 242, 255, 0.2);
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        border-radius: 8px;
    }
    
    /* INTERACTIVE ELEMENTS */
    .stButton>button {
        background: linear-gradient(45deg, #00f2ff, #0051ff);
        border: none;
        color: black;
        font-family: 'Orbitron';
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.05); box-shadow: 0 0 20px #00f2ff; }
</style>
""", unsafe_allow_html=True)

# --- 2. THE PHYSICS & RENDERING ENGINE ---

@st.cache_data
def load_data():
    """Robust Data Loader (Live + Backup)"""
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_rade,pl_masse,pl_eqt,sy_dist,st_teff,st_rad,disc_year+from+pscomppars+where+pl_rade+is+not+null+and+pl_masse+is+not+null&format=csv"
    try:
        df = pd.read_csv(url)
        df = df.rename(columns={'pl_name': 'Name', 'pl_rade': 'Radius', 'pl_masse': 'Mass', 'pl_eqt': 'Temp', 'sy_dist': 'Distance'})
        return df.dropna(), "ONLINE"
    except:
        # Emergency Data
        data = {
            'Name': ['Proxima Cen b', 'TRAPPIST-1 e', 'Kepler-442 b', 'K2-18 b'],
            'Radius': [1.03, 0.91, 1.34, 2.37],
            'Mass': [1.07, 0.77, 2.30, 8.92],
            'Temp': [234, 251, 233, 265],
            'Distance': [1.3, 12.1, 342.0, 38.0]
        }
        return pd.DataFrame(data), "OFFLINE"

def generate_procedural_planet(radius, temp, atmosphere_density):
    """
    GENESIS ENGINE: Procedurally generates a 3D sphere texture based on physics.
    Hot -> Red/Lava. Cold -> White/Ice. Habitable -> Blue/Green/Clouds.
    """
    # Create Sphere Topology
    phi = np.linspace(0, 2*np.pi, 100)
    theta = np.linspace(0, np.pi, 100)
    phi, theta = np.meshgrid(phi, theta)
    
    x = radius * np.sin(theta) * np.cos(phi)
    y = radius * np.sin(theta) * np.sin(phi)
    z = radius * np.cos(theta)
    
    # DETERMINE VISUAL CLASS (The "Game" Logic)
    if temp > 800:
        # Lava World
        colorscale = 'Hot'
        surface_color = np.random.rand(100, 100) * 0.5 + 0.5 # Volcanic noise
    elif temp > 350:
        # Desert World (Venus-like)
        colorscale = 'YlOrBr'
        surface_color = np.sin(phi*5) * np.cos(theta*5) # Dune patterns
    elif temp < 200:
        # Ice World
        colorscale = 'Blues'
        surface_color = np.random.rand(100, 100) * 0.2 # Icy noise
    elif 260 < temp < 320 and atmosphere_density > 20:
        # EARTH-LIKE (The Goal)
        colorscale = [[0, 'darkblue'], [0.4, 'blue'], [0.5, 'green'], [0.6, 'darkgreen'], [0.8, 'saddlebrown'], [1.0, 'white']]
        # Generate Continents via Perlin-ish noise (Simplified with Sin waves)
        surface_color = np.sin(phi*3) + np.cos(theta*3) + np.random.rand(100, 100)*0.5
        surface_color = (surface_color - surface_color.min()) / (surface_color.max() - surface_color.min()) # Normalize 0-1
    else:
        # Barren Rock
        colorscale = 'Gray'
        surface_color = np.random.rand(100, 100) # Craters
        
    return x, y, z, surface_color, colorscale

# --- 3. THE UI LOGIC ---

df, status = load_data()

# SIDEBAR: COMMAND DECK
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg", width=100)
    st.title("EXO-HUNTER")
    st.caption("GENESIS MODULE v5.0")
    
    mode = st.radio("SYSTEM MODE", ["🔭 GALAXY SCANNER", "🧬 GENESIS LAB (TERRAFORM)", "🚀 WARP DRIVE"], index=1)
    
    st.info(f"NETWORK STATUS: {status}")
    st.markdown("---")
    st.write("**Candidate Selection:**")
    selected_planet = st.selectbox("Load Planet Data", df['Name'].head(15))
    planet_data = df[df['Name'] == selected_planet].iloc[0]

# --- MODULE 1: GENESIS LAB (The "Wow" Factor) ---
if "GENESIS" in mode:
    col_main, col_viz = st.columns([1, 2])
    
    with col_main:
        st.header(f"// TERRAFORMING: {selected_planet}")
        st.markdown("Modify atmospheric conditions to stabilize the climate.")
        
        # CONTROLS
        gh_gas = st.slider("Greenhouse Injection (ppm)", 0, 1000, 50, help="Co2 Density")
        albedo = st.slider("Surface Albedo (Reflectivity)", 0.1, 1.0, 0.8, help="0.1 = Asphalt, 1.0 = Ice")
        water = st.slider("Hydrosphere Coverage (%)", 0, 100, 10)
        
        # PHYSICS CALCULATION
        # Simplified Stefan-Boltzmann adjustment
        base_temp = planet_data['Temp']
        new_temp = (base_temp * (1/albedo)**0.25) + (gh_gas * 0.15)
        
        # ESI CALCULATION (Habitability Score)
        esi = 1.0 - abs(new_temp - 288) / 288
        if esi < 0: esi = 0
        
        # HUD METRICS
        c1, c2 = st.columns(2)
        c1.metric("Surface Temp", f"{new_temp:.0f} K", delta=f"{new_temp-288:.0f}K from Earth")
        c2.metric("ESI Score", f"{esi:.2f}", delta="Habitability Index")
        
        if esi > 0.85:
            st.success("✅ LIFE SUPPORT STABLE")
            st.balloons()
        elif new_temp > 373:
            st.error("⚠️ CRITICAL: BOILING OCEANS")
        elif new_temp < 200:
            st.info("❄️ STATUS: FROZEN WASTELAND")
            
    with col_viz:
        # THE PROCEDURAL RENDERER
        st.subheader("ORBITAL VISUALIZATION")
        
        x, y, z, surface, colors = generate_procedural_planet(planet_data['Radius'], new_temp, gh_gas)
        
        fig = go.Figure(data=[go.Surface(
            x=x, y=y, z=z,
            surfacecolor=surface,
            colorscale=colors,
            lighting=dict(ambient=0.4, diffuse=0.9, specular=0.1, roughness=0.9), # Realistic lighting
            lightposition=dict(x=100, y=100, z=0)
        )])
        
        # Clean up the plot to look like a Hologram
        fig.update_layout(
            title=dict(text=f"LIVE SIMULATION: {selected_planet}", font=dict(color="#00f2ff")),
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                bgcolor='rgba(0,0,0,0)',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0),
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)

# --- MODULE 2: GALAXY SCANNER (Big Data) ---
elif "SCANNER" in mode:
    st.title("DEEP FIELD ARRAY")
    
    # Advanced 3D Scatter with "Hover" physics
    fig = px.scatter_3d(
        df, x='Distance', y='Temp', z='Radius',
        color='Mass', size='Radius',
        hover_name='Name',
        color_continuous_scale='Viridis',
        template='plotly_dark'
    )
    fig.update_layout(
        scene=dict(bgcolor='rgba(0,0,0,0)'), 
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#00f2ff',
        height=700
    )
    st.plotly_chart(fig, use_container_width=True)

# --- MODULE 3: WARP DRIVE (Relativity) ---
elif "WARP" in mode:
    st.title("RELATIVISTIC TRAJECTORY SOLVER")
    
    c1, c2 = st.columns(2)
    dist = planet_data['Distance']
    
    with c1:
        velocity = st.slider("WARP VELOCITY (% c)", 0.1, 0.999, 0.5)
        gamma = 1 / np.sqrt(1 - velocity**2)
        
        st.metric("Time Dilation Factor (γ)", f"{gamma:.4f}")
        st.metric("Subjective Time (Ship)", f"{(dist/velocity)/gamma:.1f} Years")
        st.metric("Observer Time (Earth)", f"{(dist/velocity):.1f} Years")
        
    with c2:
        # VISUALIZING THE "TWIN PARADOX"
        time_data = pd.DataFrame({
            'Observer': ['Astronaut', 'Earth Control'],
            'Years Aged': [(dist/velocity)/gamma, dist/velocity]
        })
        fig = px.bar(time_data, x='Years Aged', y='Observer', orientation='h', color='Observer', color_discrete_sequence=['#00f2ff', '#ff0055'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
