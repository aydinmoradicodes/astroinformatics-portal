# 🌌 Astroinformatics & Exoplanetary Transit Pipeline
**Developer:** Aydin  
**Target Program:** Combined Major in Computer Science & Statistics | University of British Columbia (UBC)  
**Live Production Application:** *[Insert Your Live Streamlit URL Here]*

---

## 🔬 Core Mission Objective
This repository houses an automated, research-grade computational signal processing pipeline designed to stream, isolate, clean, and analyze deep-space transit telemetry. By querying live archival observation data from NASA’s Kepler Space Telescope via the Mikulski Archive for Space Telescopes (MAST), the pipeline identifies subtle periodic variances in stellar flux, extracting structural boundary characteristics of extrasolar planets millions of light-years away.

The primary objective of this project is to demonstrate how data science frameworks, advanced statistical modeling, and machine learning principles serve as the premier modern "eyepiece" for 21st-century observational astronomy.

---

## 🚀 Advanced System Architecture
Unlike standard static plotting applications, this architecture features an end-to-end data refinery pipeline split into distinct programmatic layers:

1. **Dynamic Streaming Engine:** Leverages the `lightkurve` and `astropy` frameworks to run active, cached API queries directly against NASA metadata records.
2. **Signal Conditioning Subsystem:** Automatically strips instrument anomalies and handles missing entries (`.remove_nans()`). It implements a 5-sigma clipping filter (`.remove_outliers()`) to isolate cosmic ray spikes, followed by a high-pass flattening filter (`window_length=101`) to stabilize baseline stellar variability trends.
3. **Frequency Periodogram Analysis:** Deploys a **Box Least Squares (BLS)** algorithmic period search across the timeline to detect repeating box-shaped transit drops hidden inside noisy telemetry streams.
4. **Data Dimensionality Folding:** Stacks hundreds of discrete orbits on top of one another to drastically multiply the signal-to-noise ratio (SNR), rendering a pristine visual silhouette of the passing exoplanet.
5. **Interactive UI Engine:** Rendered via an enterprise-grade, midnight-neon asynchronous dashboard using `Streamlit` and `Plotly Graphs`.

---

## 📐 The Underlying Physics & Astrophysics Math
To extract physical planetary parameters without direct imaging metrics, the pipeline leverages classical transit photometry physics.

### 1. Signal Depth to Radius Ratio
The percentage drop in a star's light ($\Delta F$) during a transit is directly proportional to the cross-sectional area ratio of the planet ($\pi R_p^2$) relative to its host star ($\pi R_\star^2$):

$$\Delta F = \left(\frac{R_p}{R_\star}\right)^2$$

### 2. Physical Boundary Calculation
By algebraically isolating the planetary radius ($R_p$), the pipeline extracts the real-world scale of the world. It queries the authentic stellar radius ($R_\star$) from the Kepler Input Catalog (KIC) metadata and maps the planetary output into Jupiter Radii ($R_{Jup}$), where $1 \text{ R}_{\odot} \approx 9.731 \text{ R}_{Jup}$:

$$R_p = \sqrt{\Delta F} \times R_\star \times 9.731$$

---

## 🛠️ Local Laboratory Setup
To execute this computational workspace locally on your machine, clone this repository and initialize the Python dependencies:

```bash
# Clone the workspace
git clone https://github.com[Your-Username]/astroinformatics-portal.git
cd astroinformatics-portal

# Install scientific dependencies
pip install -r requirements.txt

# Run the local server
streamlit run app.py
```

## 📊 Sample Inputs for Reviewers
To test the pipeline's analytical power, try entering these verified targets into the Mission Control Panel:
*   **Kepler-8** (Quarter 2): Reveals a massive, rapid-orbiting Gas Giant with deep, crisp transit drops.
*   **Kepler-10** (Quarter 3): Showcases the data cleaning subsystem's capability to isolate subtle planet curves from a hyper-dense telemetry stream.
