import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CINEMATIC CONFIGURATION ---
st.set_page_config(layout="wide", page_title="ExoHunter | Genesis", page_icon="🪐")

# Injecting "Orbitron" Font & Deep Space UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500&display=swap');

    /* DEEP SPACE BACKGROUND */
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
    p, div, label, span { font-family: 'Rajdhani', sans-serif !important; color: #e0e0e0; font-size: 16px; }
    
    /* GLASSMORPHISM PANELS */
    div.stMetric, div.css-1r6slb0 {
        background: rgba(10, 20, 30, 0.8);
        border: 1px solid rgba(0, 242, 255, 0.3);
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.1);
        backdrop-filter: blur(5px);
        border-radius: 5px;
    }
    
    /* INPUT WIDGETS */
    .stSelectbox > div > div { background-color: #0b121c; color: white; border: 1px solid #00f2ff; }
    .stSlider > div > div > div > div { background-color: #00f2ff; }
</style>
""", unsafe_allow_html=True)

# --- 2. PHYSICS ENGINE (ROBUST MODE) ---

@st.cache_data
def load_data():
    """
    Robust Data Loader. 
    Filters for planets that are actually interesting (not just random rocks).
    """
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_rade,pl_masse,pl_eqt,sy_dist,st_teff,st_rad,disc_year+from+pscomppars+where+pl_rade+is+not+null+and+pl_masse+is+not+null&format=csv"
    try:
        df = pd.read_csv(url)
        df = df.rename(columns={'pl_name': 'Name', 'pl_rade': 'Radius', 'pl_masse': 'Mass', 'pl_eqt': 'Temp', 'sy_dist': 'Distance'})
        df = df.dropna()
        # Filter: Only show planets where we have a chance (Radius < 5 Earths)
        return df[df['Radius'] < 5.0].sort_values('Distance'), "ONLINE (NASA ARCHIVE)"
    except:
        # FALLBACK DATA (Guaranteed to work)
        data = {
            'Name': ['Proxima Cen b', 'TRAPPIST-1 e', 'Kepler-442 b', 'K2-18 b', 'Teegarden b'],
            'Radius': [1.03, 0.91, 1.34, 2.37, 1.02],
            'Mass': [1.07, 0.77, 2.3, 8.9, 1.05],
            'Temp': [234, 251, 233, 265, 260],
            'Distance': [1.3, 12.1, 342, 38, 3.8]
        }
        return pd.DataFrame(data), "OFFLINE (SIMULATION MODE)"

def generate_planet_texture(temp, atmosphere, albedo):
    """
    GENESIS ENGINE v2: Procedural 3D Texture Generation.
    Now accounts for Albedo (Ice) visually.
    """
    phi = np.linspace(0, 2*np.pi, 100)
    theta = np.linspace(0, np.pi, 100)
    phi, theta = np.meshgrid(phi, theta)
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(theta)
    
    # VISUAL LOGIC: The "Game" State
    if albedo > 0.85 and temp < 270:
        # SNOWBALL EARTH (High Albedo + Cold)
        colorscale = 'Blues'
        surface = np.random.rand(100, 100) * 0.2 + 0.8 # White/Blue
    elif temp > 800:
        # MAGMA WORLD
        colorscale = [[0, 'black'], [0.4, 'red'], [1, 'orange']]
        surface = np.random.rand(100, 100)
    elif temp > 350:
        # DESERT / VENUS
        colorscale = 'YlOrBr'
        surface = np.sin(phi*5) * np.cos(theta*5)
    elif 260 < temp < 310 and atmosphere > 20:
        # HABITABLE (The Goal)
        colorscale = [[0, 'navy'], [0.4, 'blue'], [0.5, 'forestgreen'], [0.6, 'green'], [0.8, 'sienna'], [1, 'white']]
        # Continents
        surface = np.sin(phi*3) + np.cos(theta*3) + np.random.rand(100, 100)*0.5
    else:
        # BARREN ROCK
        colorscale = 'Greys'
        surface = np.random.rand(100, 100)

    return x, y, z, surface, colorscale

# --- 3. UI DASHBOARD ---

df, status = load_data()

# SIDEBAR
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg", width=120)
    st.title("EXO-HUNTER")
    st.caption(f"SYSTEM STATUS: {status}")
    mode = st.radio("SELECT MODULE", ["🌌 GALAXY SCANNER", "🧬 GENESIS LAB", "🚀 WARP DRIVE"], index=1)
    
    st.markdown("---")
    if mode == "🧬 GENESIS LAB":
        st.write("**TARGET LOCK:**")
        # Smart Select: Prioritize Earth-sized planets
        candidates = df.sort_values('Distance').head(50)
        selected_planet = st.selectbox("Select Candidate", candidates['Name'])
        planet_data = df[df['Name'] == selected_planet].iloc[0]

# --- MODULE 1: GALAXY SCANNER ---
if mode == "🌌 GALAXY SCANNER":
    st.title("DEEP FIELD ARRAY")
    st.markdown("Real-time 3D plotting of confirmed exoplanets.")
    
    fig = px.scatter_3d(
        df.head(300),
        x='Distance', y='Temp', z='Radius',
        color='Mass', size='Radius',
        hover_name='Name',
        color_continuous_scale='Viridis',
        template='plotly_dark',
        title="Stellar Neighborhood (Color = Mass)"
    )
    fig.update_layout(height=700, margin=dict(l=0, r=0, b=0, t=30), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# --- MODULE 2: GENESIS LAB (THE BIG UPGRADE) ---
elif mode == "🧬 GENESIS LAB":
    st.title(f"// PLANETARY ENGINEERING: {selected_planet}")
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("### 🛠️ TERRAFORMING CONTROLS")
        
        # 1. ORBITAL MIRROR (The Coolant)
        st.info("SOLAR MANAGEMENT")
        shade = st.slider("Orbital Mirror Array (Block Light %)", 0, 99, 0, help="Deploy Lagrange-point shades to cool the planet.")
        flux_modifier = 1 - (shade / 100.0)
        
        # 2. ATMOSPHERE (The Heater)
        st.warning("ATMOSPHERIC INJECTION")
        gh_gas = st.slider("Greenhouse Density (ppm)", 0, 1000, 10, help="Inject CO2 to warm the planet.")
        
        # 3. ALBEDO (Reflectivity)
        st.success("SURFACE MODIFICATION")
        albedo = st.slider("Surface Albedo", 0.1, 1.0, 0.3, help="0.1 = Asphalt, 1.0 = Ice Mirror")
        
        # --- THE PHYSICS ENGINE ---
        # Stefan-Boltzmann Law modified for Engineering
        base_temp = planet_data['Temp']
        
        # Formula: New Temp = Base * (Flux_Mod)^0.25 * (Albedo_Factor) + Greenhouse
        # Note: We divide by albedo^0.25 because Higher Albedo = Cooler
        cooling_factor = (flux_modifier * (0.3 / albedo)) ** 0.25
        new_temp = (base_temp * cooling_factor) + (gh_gas * 0.15)
        
        # Clamp temp to absolute zero
        if new_temp < 0: new_temp = 0
        
        # ESI Calculation
        esi = 1.0 - abs(new_temp - 288) / 288
        if esi < 0: esi = 0
        
        # --- HUD METRICS ---
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("Surface Temp", f"{new_temp:.0f} K", delta=f"{new_temp - 288:.0f} K (Earth)")
        m2.metric("Habitability Score", f"{esi:.2f}", delta="ESI (Max 1.0)")
        m3.metric("Stellar Flux", f"{flux_modifier*100:.0f}%", delta="- Energy")
        
        # STATUS MESSAGE
        if 260 < new_temp < 310:
            st.success("✅ OPTIMAL: LIQUID WATER STABLE")
            st.balloons()
        elif new_temp > 373:
            st.error("⚠️ CRITICAL: SURFACE BOILING")
        elif new_temp < 200:
            st.info("❄️ CRITICAL: DEEP FREEZE")

    with c2:
        # 3D RENDERER
        x, y, z, surf, colors = generate_planet_texture(new_temp, gh_gas, albedo)
        
        fig = go.Figure(data=[go.Surface(
            x=x, y=y, z=z,
            surfacecolor=surf,
            colorscale=colors,
            lighting=dict(ambient=0.4, diffuse=0.9, roughness=0.9, specular=0.1),
            lightposition=dict(x=100, y=100, z=0)
        )])
        
        fig.update_layout(
            title=dict(text="LIVE OPTICAL FEED", x=0.5, font=dict(color="#00f2ff", size=20)),
            scene=dict(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False, bgcolor='rgba(0,0,0,0)'),
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, b=0, t=40),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

# --- MODULE 3: WARP DRIVE (SYNTAX FIXED) ---
elif mode == "🚀 WARP DRIVE":
    st.title("RELATIVITY ENGINE")
    
    c1, c2 = st.columns(2)
    with c1:
        target = st.selectbox("Destination", df['Name'].head(10))
        dist = df.loc[df['Name'] == target, 'Distance'].values[0]
        st.metric("Distance", f"{dist:.1f} Parsecs", f"{(dist*3.26):.1f} Light Years")
    with c2:
        velocity = st.slider("Warp Velocity (% c)", 0.1, 0.999, 0.5, 0.001)
    
    # Physics
    gamma = 1 / np.sqrt(1 - velocity**2)
    ship_time = (dist * 3.26) / velocity / gamma
    earth_time = (dist * 3.26) / velocity
    
    # GAUGES (Syntax Error Fixed Here)
    st.markdown("---")
    g1, g2, g3 = st.columns(3)
    
    # The fix: 'range': [0, 20] instead of 'range': }
    fig_gamma = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = gamma,
        title = {'text': "Time Dilation (γ)"},
        gauge = {'axis': {'range': [1, 20]}, 'bar': {'color': "#00f2ff"}, # <--- FIXED
                 'steps': [{'range': [0, 5], 'color': "#333"}]}
    ))
    fig_gamma.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Orbitron"})
    g1.plotly_chart(fig_gamma, use_container_width=True)
    
    g2.metric("Subjective Time (You)", f"{ship_time:.1f} Years", "Aged Less")
    g3.metric("Observer Time (Earth)", f"{earth_time:.1f} Years", "Aged More")
