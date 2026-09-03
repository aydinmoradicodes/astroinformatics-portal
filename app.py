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
    
    /* NEON METRIC BOXES */
    div.stMetric {
        background: rgba(10, 20, 30, 0.8);
        border: 1px solid rgba(0, 242, 255, 0.3);
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.1);
        backdrop-filter: blur(5px);
        border-radius: 5px;
        padding: 10px;
    }
    
    /* CUSTOM BUTTONS & SELECTBOXES */
    .stSelectbox > div > div { background-color: #0b121c; color: white; border: 1px solid #00f2ff; }
    .stSlider > div > div > div > div { background-color: #00f2ff; }
</style>
""", unsafe_allow_html=True)

# --- 2. PHYSICS ENGINE (ROBUST MODE) ---

@st.cache_data
def load_data():
    """Robust Data Loader with Emergency Backup"""
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,pl_rade,pl_masse,pl_eqt,sy_dist,st_teff,st_rad,disc_year+from+pscomppars+where+pl_rade+is+not+null+and+pl_masse+is+not+null&format=csv"
    try:
        df = pd.read_csv(url)
        df = df.rename(columns={'pl_name': 'Name', 'pl_rade': 'Radius', 'pl_masse': 'Mass', 'pl_eqt': 'Temp', 'sy_dist': 'Distance'})
        return df.dropna(), "ONLINE (NASA ARCHIVE)"
    except:
        # FALLBACK DATA (Prevents Crash)
        data = {
            'Name': ['Proxima Cen b', 'TRAPPIST-1 e', 'Kepler-442 b', 'K2-18 b', 'Wolf 1061 c'],
            'Radius': [1.03, 0.92, 1.34, 2.61, 1.66],
            'Mass': [1.07, 0.69, 2.34, 8.63, 4.26],
            'Temp': [234, 251, 260, 265, 223],
            'Distance': [1.3, 12.1, 342, 38, 4.3]
        }
        return pd.DataFrame(data), "OFFLINE (SIMULATION MODE)"

def generate_planet_texture(temp, atmosphere):
    """
    GENESIS ENGINE: Procedural 3D Texture Generation.
    Links Thermodynamics -> Visual Color Mapping.
    """
    # Sphere Topology
    phi = np.linspace(0, 2*np.pi, 100)
    theta = np.linspace(0, np.pi, 100)
    phi, theta = np.meshgrid(phi, theta)
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(theta)
    
    # Visual Logic (The "Game" Part)
    if temp > 800:
        # LAVA WORLD
        colorscale = [[0, 'black'], [0.5, 'red'], [1, 'orange']]
        noise = np.random.rand(100, 100) * 0.4 # Magma flows
        surface = noise + 0.5
    elif temp > 350:
        # DESERT/VENUS
        colorscale = 'YlOrBr'
        surface = np.sin(phi*5) * np.cos(theta*5) # Dunes
    elif 250 < temp < 320 and atmosphere > 20:
        # EARTH-LIKE (Habitable)
        colorscale = [[0, 'navy'], [0.4, 'blue'], [0.5, 'forestgreen'], [0.6, 'green'], [0.8, 'sienna'], [1, 'white']]
        surface = np.sin(phi*3) + np.cos(theta*3) + np.random.rand(100, 100)*0.5
    else:
        # DEAD ROCK / ICE
        colorscale = 'Greys' if temp > 200 else 'Blues'
        surface = np.random.rand(100, 100) # Craters

    return x, y, z, surface, colorscale

# --- 3. UI DASHBOARD ---

df, status = load_data()

# SIDEBAR (LOGO IS BACK)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg", width=120)
    st.title("EXO-HUNTER")
    st.caption(f"SYSTEM STATUS: {status}")
    mode = st.radio("SELECT MODULE", ["🌌 GALAXY SCANNER", "🧬 GENESIS LAB", "🚀 WARP DRIVE"], index=1)
    
    st.markdown("---")
    if mode == "🧬 GENESIS LAB":
        st.write("**TARGET LOCK:**")
        # Ensure we only pick valid names
        valid_names = df['Name'].head(15).tolist()
        selected_planet = st.selectbox("Select Candidate", valid_names)
        # FIX: Robust Data Selection
        planet_data = df[df['Name'] == selected_planet].iloc[0]

# --- MODULE 1: GALAXY SCANNER ---
if mode == "🌌 GALAXY SCANNER":
    st.title("DEEP FIELD ARRAY")
    st.markdown("Real-time 3D plotting of confirmed exoplanets.")
    
    # 3D Scatter Plot
    fig = px.scatter_3d(
        df.head(200), # Limit to 200 for speed
        x='Distance', y='Temp', z='Radius',
        color='Mass', size='Radius',
        hover_name='Name',
        color_continuous_scale='Viridis',
        template='plotly_dark',
        title="Local Stellar Neighborhood (Mass/Radius Distribution)"
    )
    
    fig.update_layout(
        scene=dict(
            bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='#333'),
            yaxis=dict(gridcolor='#333'),
            zaxis=dict(gridcolor='#333'),
        ), 
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#00f2ff',
        height=700,
        margin=dict(l=0, r=0, b=0, t=30)
    )
    st.plotly_chart(fig, use_container_width=True)

# --- MODULE 2: GENESIS LAB (FIXED LAYOUT) ---
elif mode == "🧬 GENESIS LAB":
    # FIX: Explicitly defined columns (2) to prevent TypeError
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader(f"// ENGINEERING: {selected_planet}")
        
        # Interactive Physics Sliders
        gh_gas = st.slider("Greenhouse Density (ppm)", 0, 1000, 50)
        albedo = st.slider("Surface Albedo", 0.1, 1.0, 0.8)
        
        # Real-time Calculation
        base_temp = planet_data['Temp']
        # Simplified Greenhouse Formula
        new_temp = (base_temp * (1/albedo)**0.25) + (gh_gas * 0.15)
        esi = 1.0 - abs(new_temp - 288) / 288
        if esi < 0: esi = 0
        
        # HUD Metrics
        st.markdown("---")
        # FIX: Nested columns for metrics
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Surface Temp", f"{new_temp:.0f} K", delta=f"{new_temp-288:.0f} K")
        col_m2.metric("Habitability", f"{esi:.2f}", delta="ESI Score")
        
        st.markdown("### STATUS REPORT")
        if 260 < new_temp < 310:
            st.success("✅ BIOSPHERE STABLE: LIQUID WATER DETECTED")
        elif new_temp > 373:
            st.error("⚠️ CRITICAL FAILURE: WATER BOILING")
        else:
            st.info("❄️ CRITICAL FAILURE: SURFACE FROZEN")

    with c2:
        # The 3D Planet Renderer
        x, y, z, surf, colors = generate_planet_texture(new_temp, gh_gas)
        
        fig = go.Figure(data=[go.Surface(
            x=x, y=y, z=z,
            surfacecolor=surf,
            colorscale=colors,
            lighting=dict(ambient=0.4, diffuse=0.9, roughness=0.9, specular=0.1),
            lightposition=dict(x=100, y=100, z=0)
        )])
        
        fig.update_layout(
            title=dict(text="LIVE OPTICAL FEED", x=0.5, font=dict(color="#00f2ff", size=20)),
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                bgcolor='rgba(0,0,0,0)',
                camera=dict(eye=dict(x=1.6, y=1.6, z=1.6))
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, b=0, t=40),
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)

# --- MODULE 3: WARP DRIVE (FIXED PANDAS BUG) ---
elif mode == "🚀 WARP DRIVE":
    st.title("RELATIVITY ENGINE")
    st.markdown("Time Dilation Simulator (Lorentz Factor Calculator)")
    
    # 1. Inputs
    # FIX: Defined 2 columns
    c1, c2 = st.columns(2)
    with c1:
        target = st.selectbox("Destination", df['Name'].head(10))
        # FIX: Correct way to get scalar value from Pandas
        dist = df.loc[df['Name'] == target, 'Distance'].values[0]
        st.metric("Distance", f"{dist:.1f} Parsecs", f"{(dist*3.26):.1f} Light Years")
    with c2:
        velocity = st.slider("Warp Velocity (% c)", 0.1, 0.999, 0.5, 0.001)
    
    # 2. Physics
    gamma = 1 / np.sqrt(1 - velocity**2)
    ship_time = (dist * 3.26) / velocity / gamma
    earth_time = (dist * 3.26) / velocity
    
    # 3. New Visuals: COCKPIT GAUGES
    st.markdown("---")
    # FIX: Defined 3 columns
    g1, g2, g3 = st.columns(3)
    
    # Gauge 1: Time Dilation
    fig_gamma = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = gamma,
        title = {'text': "Time Dilation (γ)"},
        gauge = {'axis': {'range': [1, 20]}, 'bar': {'color': "#00f2ff"},
                 'steps': [{'range': [0, 5], 'color': "#333"}, {'range': [5, 20], 'color': "#111"}]}
    ))
    fig_gamma.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Orbitron"})
    g1.plotly_chart(fig_gamma, use_container_width=True)
    
    # Gauge 2: Ship Clock
    g2.metric("Subjective Time (You)", f"{ship_time:.1f} Years", "Aged Less")
    
    # Gauge 3: Earth Clock
    g3.metric("Observer Time (Earth)", f"{earth_time:.1f} Years", "Aged More")
    
    # Comparison Chart
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(
        y=['Years Passed'], x=[ship_time], name='Astronaut', orientation='h', marker_color='#00f2ff'
    ))
    fig_comp.add_trace(go.Bar(
        y=['Years Passed'], x=[earth_time], name='Earth Control', orientation='h', marker_color='#ff0055'
    ))
    fig_comp.update_layout(
        title="THE TWIN PARADOX",
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font_color='white', xaxis_title="Years",
        height=300
    )
    st.plotly_chart(fig_comp, use_container_width=True)
