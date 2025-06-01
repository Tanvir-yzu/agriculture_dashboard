# agriculture_dashboard.py

import streamlit as st
import matplotlib.pyplot as plt
from simulation import run_simulation

st.set_page_config(page_title="Smart Agriculture Simulator", layout="wide")
st.title("🌿 Smart Agriculture Simulator Dashboard")
st.markdown("Simulate crop yield, soil conditions, and resource usage with smart farming practices.")

# Sidebar Controls
st.sidebar.header("🌾 Simulation Settings")
farm_size = st.sidebar.slider("Farm Size (hectares)", 1, 100, 10)
crop_type = st.sidebar.selectbox("Crop Type", ["wheat", "corn", "soy", "tomato"])
simulation_days = st.sidebar.slider("Simulation Days", 30, 180, 120)

if st.sidebar.button("🚀 Run Simulation"):
    with st.spinner("Running simulation..."):
        report, data = run_simulation(farm_size=farm_size, crop_type=crop_type, duration=simulation_days, return_data=True)

    st.success("Simulation Complete!")

    # Summary Report
    st.subheader("📋 Summary Report")
    st.json(report)

    # Charts
    st.subheader("📊 Daily Metrics")

    fig, axs = plt.subplots(2, 2, figsize=(14, 10))

    axs[0, 0].plot(data["day"], data["soil_moisture"], label="Soil Moisture")
    axs[0, 0].plot(data["day"], data["soil_N"], label="Soil Nitrogen (N)")
    axs[0, 0].set_title("Soil Conditions")
    axs[0, 0].legend()
    axs[0, 0].grid()

    axs[0, 1].plot(data["day"], data["crop_growth"] * 100, color="green")
    axs[0, 1].set_title("Crop Growth (%)")
    axs[0, 1].grid()

    axs[1, 0].bar(data["day"], data["fertilizer"], color="orange", label="Fertilizer")
    axs[1, 0].plot(data["day"], data["irrigation"], color="blue", label="Irrigation")
    axs[1, 0].set_title("Resource Inputs")
    axs[1, 0].legend()
    axs[1, 0].grid()

    axs[1, 1].plot(data["day"], data["pest_pressure"] * 100, color="red", label="Pest Pressure (%)")
    axs[1, 1].set_title("Pest Pressure")
    axs[1, 1].legend()
    axs[1, 1].grid()

    st.pyplot(fig)

else:
    st.info("Select parameters and click **Run Simulation** to begin.")
