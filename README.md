# LandslideGuard AI 🏔️

**Live Deployment:** [Launch Command Center](https://landslideguard-ai-kh7h6j3gm24baq6eor87qz.streamlit.app)

**Problem Statement:** SIH 2026 PS26001  
**Institution:** Seth Jai Parkash Mukand Lal Institute of Engineering and Technology (JMIT)  
**Team Leader:** Sameer Verma 

## Overview
LandslideGuard AI is a prototype Command & Control System designed for North Eastern Region (NER) disaster intelligence. It replaces traditional, static early warning nodes with real-time, predictive 3D spatial intelligence and edge-resilient offline reporting.

## Key Features
* **Dynamic AI Risk Scoring:** Scikit-Learn machine learning pipeline dynamically scores risk using live variables (slope angle, soil moisture, and cumulative rainfall).
* **3D Spatial Intelligence:** Interactive PyDeck terrain mapping generates immediate, visual threat assessments (Low to Critical).
* **"What-If" Simulator:** Allows authorities to manually inject environmental anomalies (e.g., a 200mm rainfall surge) to stress-test predictive risk in real-time.
* **Edge Resilience:** SQLite database integration ensures citizen ground-observation reports are preserved locally and synced even during mountain network blackouts.

## Local Installation
To run this project locally for development or testing:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/sameer-verma-07/landslideguard-ai.git](https://github.com/sameer-verma-07/landslideguard-ai.git)
   cd landslideguard-ai
