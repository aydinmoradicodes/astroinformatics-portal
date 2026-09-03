# 🪐 ExoHunter: Genesis
**A Computational Astrobiology & Planetary Engineering Suite.**

### 🚀 Mission
ExoHunter is a Python-based physics engine designed to simulate habitability solutions for exoplanets. It connects to the **NASA Exoplanet Archive** to retrieve live telemetry and allows users to model terraforming scenarios using thermodynamic principles.

### 🧬 Core Innovation: The Genesis Engine
Most visualization tools use static images. ExoHunter uses a **Procedural Texture Algorithm** (NumPy) to render 3D planetary surfaces in real-time.
*   **The Math:** The visual texture is derived directly from the **Stefan-Boltzmann Law**.
*   **The Simulation:** If a user deploys the **Orbital Mirror Array** (reducing Stellar Flux), the texture engine detects the temperature drop and dynamically shifts the surface generation from "Magma" to "Ocean" or "Ice".

### 🛠️ Modules
1.  **Galaxy Scanner:** 3D plotting of our local stellar neighborhood using Plotly WebGL.
2.  **Genesis Lab:** A sandbox for testing the "Schulze-Makuch" Earth Similarity Index (ESI) under different atmospheric conditions.
3.  **Relativity Engine:** A calculator for Time Dilation (Lorentz Factors) during high-velocity interstellar travel.

### 👨‍💻 Tech Stack
*   **Language:** Python 3.11
*   **Libraries:** Streamlit, Plotly, Pandas, NumPy
*   **Data:** NASA TAP Service (Auto-Failover)
