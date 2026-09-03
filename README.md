# 🪐 ExoHunter: Genesis
**Computational Astrophysics & Planetary Engineering Suite**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

### 🚀 Project Overview
ExoHunter is a full-stack Python application designed to simulate the terraforming of exoplanets using real telemetry from the **NASA Exoplanet Archive**. Unlike standard visualization tools, this engine solves a core problem in astrobiology: **Stellar Flux Management**.

Most exoplanets orbit too close to their host stars to support liquid water. ExoHunter implements a **Lagrange-Point Solar Shade** simulation, allowing users to reduce incoming stellar flux and lower the equilibrium temperature of "Hot Super-Earths" into the habitable range.

### 🧬 Core Features
*   **Genesis Engine (Procedural Rendering):** Uses NumPy noise algorithms to generate 3D planetary surfaces in real-time. The surface texture dynamically shifts (Magma ↔ Desert ↔ Ocean ↔ Ice) based on the calculated thermodynamic state.
*   **Engineering Lab:** Users can manipulate:
    *   **Albedo:** Surface reflectivity modification.
    *   **Greenhouse Gases:** Atmospheric injection (ppm).
    *   **Orbital Mirrors:** Stellar flux reduction (Lagrange engineering).
*   **Relativity Solver:** A special relativity calculator that visualizes Time Dilation (Lorentz Factors) and the "Twin Paradox" for interstellar trajectories.

### 🛠️ Tech Stack
*   **Physics:** Stefan-Boltzmann Law, Lorentz Transformations
*   **Backend:** Python 3.10, Pandas (Data Analysis)
*   **Frontend:** Streamlit (Custom CSS/HUD), Plotly (3D WebGL Rendering)
*   **Data:** NASA TAP API (Automated Failover Protocol)

### 👨‍💻 Created By Aydin
*Passionate about the intersection of Computer Science, Data Visualization, and Astrophysics.*
