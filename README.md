# 🪐 ExoHunter: Genesis
**Computational Astrophysics & Planetary Engineering Suite**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

### 🚀 Mission
ExoHunter is a sophisticated physics engine designed to simulate habitability solutions for exoplanets. It connects to the **NASA Exoplanet Archive** to retrieve live telemetry and allows users to model terraforming scenarios using thermodynamic principles.

### 🧬 Core Innovation: The Genesis Engine
Most visualization tools use static images. ExoHunter uses a **Procedural Texture Algorithm** (NumPy) to render 3D planetary surfaces in real-time.
*   **The Math:** The visual texture is derived directly from the **Stefan-Boltzmann Law**.
*   **The Simulation:** Users can deploy an **Orbital Mirror Array** to block stellar flux, dynamically cooling a "Magma World" (700K) into a habitable "Ocean World" (288K).

### 🛠️ Modules
1.  **Galaxy Scanner:** Real-time 3D plotting of our local stellar neighborhood.
2.  **Genesis Lab:** A sandbox for testing the "Schulze-Makuch" Earth Similarity Index (ESI) under different atmospheric conditions.
3.  **Relativity Engine:** A calculator for Time Dilation (Lorentz Factors) during high-velocity interstellar travel.

### 👨‍💻 Tech Stack
*   **Physics:** Stefan-Boltzmann Law, Lorentz Transformations
*   **Backend:** Python 3.11, Pandas
*   **Frontend:** Streamlit (Custom Glassmorphism CSS), Plotly WebGL
*   **Data:** NASA TAP Service
