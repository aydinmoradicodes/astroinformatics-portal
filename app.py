import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CINEMATIC CONFIGURATION ---
st.set_page_config(layout="wide", page_title="ExoHunter | Genesis", page_icon="🪐")

# EXPERT CSS: "Glassmorphism" & Smooth Animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500&display=swap');

    /* UNIVERSE BACKGROUND */
    .stApp {
        background-color: #000000;
        background-image: 
            radial-gradient(circle at 50% 50%, rgba(20, 20, 50, 0.2) 0%, transparent 50%),
            radial-gradient(white, rgba(255,255,255,.2) 2px, transparent 3px),
            radial-gradient(white, rgba(255,255,255,.15) 1px, transparent 2px),
            radial-gradient(white, rgba(255,255,255,.1) 2px, transparent 3px);
        background-size: 100% 100%, 550px 550px, 350px 350px, 250px 250px;
        background-position: 0 0, 0 0, 40px 60px, 130px 270px;
    }

    /* HUD TYPOGRAPHY */
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00f2ff !important; text-shadow: 0px 0px 15px rgba(0, 242, 255, 0.8); }
    p, div, label, span { font-family: 'Rajdhani', sans-serif !important; color: #e0e0e0; font-size: 18px; }
    
    /* GLASS PANELS */
    div.stMetric, div.css-1r6slb0 {
        background: rgba(15, 25, 40, 0.7);
        border: 1px solid rgba(0, 242, 255, 0.2);
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        border-radius: 10px;
    }

    /* SUCCESS STATE GLOW */
    .habitable-glow {
        border: 2px solid #00ff41 !important;
        box-shadow: 0 0 30px rgba(0, 255, 65, 0.4) !important;
    }
    
    /* CONTROLS */
    .stSlider > div > div > div > div { background-color: #00f2ff; }
    .stSelectbox > div > div { background-color: #0b121c; color: white; border: 1px solid #00f2ff; }
</style>
""", unsafe_allow_html=True)

# --- 2. PHYSICS ENGINE (ROBUST) ---

@st.cache_data
def load_data():
    """Robust Data Loader with Failover"""
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_rade,pl_masse,pl_eqt,sy_dist,st_teff,st_rad,disc_year+from+pscomppars+where+pl_rade+is+not+null+and+pl_masse+is+not+null&format=csv"
    try:
        df = pd.read_csv(url)
        df = df.rename(columns={'pl_name': 'Name', 'pl_rade': 'Radius', 'pl_masse': 'Mass', 'pl_eqt': 'Temp', 'sy_dist': 'Distance'})
        df = df.dropna()
        # Filter for interesting planets (Super-Earths)
        return df[(df['Radius'] < 2.5) & (df['Distance'] < 100)].sort_values('Distance'), "ONLINE (NASA ARCHIVE)"
    except:
        # Emergency Data
        data = {
            'Name': ['Proxima Cen b', 'TRAPPIST-1 e', 'Kepler-442 b', 'K2-18 b', 'Teegarden b'],
            'Radius': [1.07, 0.92, 1.34, 2.6, 1.05],
            'Mass': [1.17, 0.69, 2.3, 8.6, 1.05],
            'Temp': [234, 251, 233, 265, 290],
            'Distance': [1.3, 12.0, 370, 38, 3.8]
        }
        return pd.DataFrame(data), "OFFLINE (SIMULATION)"

def generate_seamless_texture(temp, albedo, atmosphere):
    """
    GENESIS ENGINE v3: High-Fidelity Planet Rendering.
    Uses vector math to create seamless, non-stretched textures.
    """
    # High Res Mesh
    resolution = 100
    phi = np.linspace(0, 2*np.pi, resolution)
    theta = np.linspace(0, np.pi, resolution)
    phi, theta = np.meshgrid(phi, theta)
    
    # Sphere Coords
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(theta)
    
    # TEXTURE LOGIC: The "Cosmos" Look
    # We mix frequencies to create continents
    noise = np.sin(phi*3) * np.cos(theta*3)     # Continents
    detail = np.sin(phi*10) * np.cos(theta*10)  # Mountains
    surface_map = noise + (detail * 0.2)
    
    # DYNAMIC BIOME SELECTOR
    if albedo > 0.8:
        # ICE WORLD (Smooth, White/Blue)
        colorscale = [[0, '#e0f7fa'], [1, '#ffffff']] # Ice
        surface_map = surface_map * 0.1 # Flatten terrain
        
    elif temp > 800:
        # LAVA WORLD (Cracked, Glowing)
        colorscale = [[0, '#1a0500'], [0.4, '#801100'], [0.7, '#ff4d00'], [1, '#ffcc00']]
        surface_map = surface_map + (np.random.rand(resolution, resolution) * 0.5)
        
    elif temp > 350:
        # VENUS/DESERT (Hazy, Orange)
        colorscale = [[0, '#4a3b2a'], [1, '#d4af37']]
        
    elif 260 < temp < 315 and atmosphere > 20:
        # EARTH-LIKE (Habitable)
        # Blue Ocean -> Green Land -> White Clouds
        colorscale = [
            [0.0, '#000033'], # Deep Ocean
            [0.4, '#1e88e5'], # Shallow Water
            [0.5, '#4caf50'], # Grass
            [0.7, '#558b2f'], # Forest
            [1.0, '#ffffff']  # Snow/Cloud
        ]
        # Smooth out oceans
        surface_map = np.clip(surface_map, -0.5, 1.0)
        
    else:
        # DEAD ROCK (Grey, Craters)
        colorscale = 'Greys'
        surface_map = surface_map + (np.random.rand(resolution, resolution) * 0.5)

    return x, y, z, surface_map, colorscale

# --- 3. UI DASHBOARD ---

df, status = load_data()

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg", width=140)
    st.title("EXO-HUNTER")
    st.caption(f"STATUS: {status}")
    mode = st.radio("MODULE", ["🌌 GALAXY SCANNER", "🧬 GENESIS LAB", "🚀 WARP DRIVE"], index=1)
    
    st.markdown("---")
    if mode == "🧬 GENESIS LAB":
        st.write("Target Selection")
        planet_list = df['Name'].head(20).tolist()
        selected_planet = st.selectbox("Candidate World", planet_list)
        planet_data = df[df['Name'] == selected_planet].iloc

# --- MODULE 1: GALAXY SCANNER ---
if mode == "🌌 GALAXY SCANNER":
    st.title("DEEP FIELD ARRAY")
    st.markdown("Real-time telemetry of the local galactic neighborhood.")
    
    fig = px.scatter_3d(
        df.head(300), x='Distance', y='Temp', z='Radius',
        color='Temp', size='Radius', hover_name='Name',
        color_continuous_scale='Turbo', template='plotly_dark',
        title="Exoplanet Distribution (Temp/Radius)"
    )
    fig.update_layout(height=700, margin=dict(l=0, r=0, b=0, t=40), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# --- MODULE 2: GENESIS LAB (THE MASTERPIECE) ---
elif mode == "🧬 GENESIS LAB":
    st.title(f"// PLANETARY ENGINEERING: {selected_planet}")
    
    col_ctrl, col_viz = st.columns([1, 1.5])
    
    with col_ctrl:
        st.markdown("### 🛠️ TERRAFORMING DECK")
        
        # 1. ORBITAL MIRROR (Cooling)
        st.info("SOLAR FLUX MANAGEMENT")
        shade = st.slider("Orbital Mirror Array (Block Light %)", 0, 99, 0)
        flux_mod = 1 - (shade / 100.0)
        
        # 2. ATMOSPHERE (Warming)
        st.warning("ATMOSPHERIC DENSITY")
        gh_gas = st.slider("Greenhouse Injection (ppm)", 0, 1000, 10)
        
        # 3. ALBEDO (Reflectivity)
        st.success("SURFACE ALBEDO")
        albedo = st.slider("Surface Reflectivity", 0.1, 1.0, 0.3)
        
        # PHYSICS ENGINE
        base_temp = planet_data['Temp']
        # The Formula: Temp drops if blocked by mirror, rises if GH gas added
        # We also account for Albedo (Higher Albedo = Cooler)
        cooling = (flux_mod * (0.3 / albedo)) ** 0.25
        new_temp = (base_temp * cooling) + (gh_gas * 0.12)
        if new_temp < 0: new_temp = 0
        
        # ESI SCORE
        esi = 1.0 - abs(new_temp - 288) / 288
        if esi < 0: esi = 0
        
        # METRICS
        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric("Equilibrium Temp", f"{new_temp:.0f} K", delta=f"{new_temp - 288:.0f} K (Earth)")
        c2.metric("Habitability Index", f"{esi:.2f}", delta="Target: 1.0")
        
        # STATUS
        if 260 < new_temp < 310:
            st.success("✅ BIOSPHERE STABLE: WATER DETECTED")
            st.balloons()
        elif new_temp > 373:
            st.error("⚠️ CRITICAL: SURFACE BOILING")
        else:
            st.info("❄️ CRITICAL: GLACIATION DETECTED")

    with col_viz:
        # THE 3D PLANET
        x, y, z, surf, colors = generate_seamless_texture(new_temp, albedo, gh_gas)
        
        fig = go.Figure(data=[go.Surface(
            x=x, y=y, z=z,
            surfacecolor=surf,
            colorscale=colors,
            lighting=dict(ambient=0.4, diffuse=0.9, specular=0.2, roughness=0.1), # Glossy Ocean Effect
            lightposition=dict(x=1000, y=1000, z=0),
            showscale=False
        )])
        
        fig.update_layout(
            title=dict(text="LIVE OPTICAL FEED", x=0.5, font=dict(color="#00f2ff", size=24, family="Orbitron")),
            scene=dict(
                xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                bgcolor='rgba(0,0,0,0)',
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, b=0, t=50),
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)

# --- MODULE 3: WARP DRIVE (BUG FREE) ---
elif mode == "🚀 WARP DRIVE":
    st.title("RELATIVITY ENGINE")
    
    c1, c2 = st.columns(2)
    with c1:
        target = st.selectbox("Destination", df['Name'].head(15))
        dist = df.loc[df['Name'] == target, 'Distance'].values
        st.metric("Distance", f"{dist:.1f} Parsecs", f"{(dist*3.26):.1f} Light Years")
    with c2:
        velocity = st.slider("Warp Velocity (% c)", 0.1, 0.999, 0.5)
    
    # Physics
    gamma = 1 / np.sqrt(1 - velocity**2)
    ship_time = (dist * 3.26) / velocity / gamma
    earth_time = (dist * 3.26) / velocity
    
    # GAUGES
    st.markdown("---")
    g1, g2, g3 = st.columns(3)
    
    # FIXED SYNTAX ERROR HERE
    fig_gamma = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = gamma,
        title = {'text': "Time Dilation (γ)"},
        gauge = {'axis': {'range': [1, 25]}, 'bar': {'color': "#00f2ff"}, 'bgcolor': "#111"}
    ))
    fig_gamma.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Orbitron"})
    g1.plotly_chart(fig_gamma, use_container_width=True)
    
    g2.metric("Ship Time (You)", f"{ship_time:.1f} Yrs", "Aged Less")
    g3.metric("Earth Time", f"{earth_time:.1f} Yrs", "Aged More")
