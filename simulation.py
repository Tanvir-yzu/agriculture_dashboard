# simulation.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class VirtualFarm:
    def __init__(self, size_ha=10, crop_type="wheat", simulation_days=120):
        self.size = size_ha  # hectares
        self.crop_type = crop_type
        self.simulation_days = simulation_days
        self.day_counter = 0

        # Environmental state
        self.soil_moisture = np.random.uniform(0.2, 0.5, size=(self.size,))
        self.soil_nutrients = {"N": 50.0, "P": 30.0, "K": 40.0}  # ppm
        self.pest_pressure = 0.1  # 0-1

        # Crop state
        self.crop_growth_stage = 0.0  # 0-1

        # Resource usage
        self.water_used = 0.0
        self.fertilizer_applied = 0.0
        self.irrigation_applied = 0.0

        # Logging
        self.daily_logs = []

    def simulate_day(self):
        # Environmental dynamics
        evapotranspiration = np.random.uniform(0.01, 0.03)
        rainfall = np.random.choice([0, 0.01, 0.05, 0.1], p=[0.7, 0.2, 0.08, 0.02])
        irrigation = 0

        avg_moisture = np.mean(self.soil_moisture)

        # Smart irrigation: trigger if below threshold
        if avg_moisture < 0.25:
            irrigation = 0.05
            self.soil_moisture += irrigation
            self.irrigation_applied += irrigation * self.size
            self.water_used += irrigation * self.size

        self.soil_moisture += rainfall - evapotranspiration
        self.soil_moisture = np.clip(self.soil_moisture, 0, 1)

        # Nutrient depletion
        nutrient_uptake = 0.3 * self.crop_growth_stage
        self.soil_nutrients["N"] = max(0, self.soil_nutrients["N"] - nutrient_uptake)

        # Smart fertilization
        if self.soil_nutrients["N"] < 20:
            self.soil_nutrients["N"] += 10
            self.fertilizer_applied += 10

        # Pest pressure increase
        self.pest_pressure += np.random.uniform(-0.01, 0.02)
        self.pest_pressure = np.clip(self.pest_pressure, 0, 1)

        # Growth
        growth_rate = (avg_moisture * 0.4 + self.soil_nutrients["N"] / 100 * 0.3 +
                       (1 - self.pest_pressure) * 0.3)
        self.crop_growth_stage += 0.01 * growth_rate
        self.crop_growth_stage = min(1.0, self.crop_growth_stage)

        self.day_counter += 1

        self.daily_logs.append({
            'day': self.day_counter,
            'soil_moisture': avg_moisture,
            'soil_N': self.soil_nutrients["N"],
            'pest_pressure': self.pest_pressure,
            'crop_growth': self.crop_growth_stage,
            'water_used': self.water_used,
            'irrigation': irrigation * self.size,
            'fertilizer': self.fertilizer_applied
        })

        return self.crop_growth_stage < 1.0 and self.day_counter < self.simulation_days

    def advance_day(self):
        return self.simulate_day()

    def generate_report(self):
        df = pd.DataFrame(self.daily_logs)
        yield_kg = self.crop_growth_stage * self.size * 1000
        return {
            "total_days": self.day_counter,
            "final_crop_growth": round(self.crop_growth_stage, 2),
            "estimated_yield_kg": round(yield_kg),
            "total_water_used_liters": round(self.water_used * 1000),
            "total_fertilizer_applied_kg": round(self.fertilizer_applied, 2),
            "final_soil_N_ppm": round(self.soil_nutrients["N"], 2),
            "final_pest_pressure": round(self.pest_pressure, 2)
        }

def run_simulation(farm_size=10, crop_type="wheat", duration=120, return_data=False):
    farm = VirtualFarm(size_ha=farm_size, crop_type=crop_type, simulation_days=duration)
    while farm.advance_day():
        pass
    report = farm.generate_report()
    data_df = pd.DataFrame(farm.daily_logs)
    return (report, data_df) if return_data else report
