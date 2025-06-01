import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random
import json

# =============================================
# SIMULATION CORE FRAMEWORK
# =============================================

class VirtualFarm:
    def __init__(self, size_ha=10, crop_type='wheat', soil_type='loam', 
                 simulation_days=120, start_date='2025-03-01'):
        self.size = size_ha
        self.crop = crop_type
        self.soil = soil_type
        self.days = simulation_days
        self.current_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.day_counter = 0
        
        self.soil_moisture = self.initialize_soil_moisture()
        self.soil_nutrients = {'N': 50, 'P': 30, 'K': 40}
        self.crop_growth_stage = 0
        self.pest_pressure = 0
        self.weather = self.generate_weather_profile()
        self.irrigation_applied = 0
        self.fertilizer_applied = 0
        self.water_used = 0
        self.yield_kg = 0
        
        self.costs = {'system': 0, 'water': 0, 'fertilizer': 0, 'labor': 0}
        self.revenue = 0
        
        self.sensor_network = SensorNetwork(self)
    
    def initialize_soil_moisture(self):
        if self.soil == 'sandy':
            return np.random.uniform(15, 25, 3)
        elif self.soil == 'clay':
            return np.random.uniform(30, 40, 3)
        else:
            return np.random.uniform(20, 30, 3)
    
    def generate_weather_profile(self):
        days = np.arange(self.days)
        temperature = 15 + 10 * np.sin(2*np.pi*days/self.days)
        rainfall = np.maximum(0, 5 * np.random.weibull(0.8, self.days))
        evapotranspiration = 0.5 * temperature + np.random.normal(2, 0.5, self.days)
        
        if self.crop == 'wheat':
            heat_wave = np.zeros(self.days)
            heat_wave[40:45] = 8
            temperature += heat_wave
            
            drought = np.zeros(self.days)
            drought[60:80] = -0.7
            rainfall = np.maximum(0, rainfall + drought)
        
        return pd.DataFrame({
            'day': days,
            'temperature': np.round(temperature, 1),
            'rainfall': np.round(rainfall, 1),
            'evapotranspiration': np.round(evapotranspiration, 1)
        })
    
    def advance_day(self):
        if self.day_counter >= self.days:
            return False
        
        today = self.weather.iloc[self.day_counter]
        self.update_soil_moisture(today)
        self.update_crop_growth(today)
        self.update_pest_pressure(today)
        
        sensor_data = self.sensor_network.collect_data()
        decisions = self.decision_engine(sensor_data, today)
        self.execute_actions(decisions)
        self.update_economics()
        
        self.day_counter += 1
        self.current_date += timedelta(days=1)
        return True
    
    def update_soil_moisture(self, weather):
        depletion = 0.7 * weather.evapotranspiration + np.random.normal(0, 0.2)
        rainfall_effect = 0.6 * weather.rainfall
        self.soil_moisture = np.maximum(0, self.soil_moisture - depletion + rainfall_effect)
        self.water_used += depletion
    
    def update_crop_growth(self, weather):
        base_growth = 0.008 * min(weather.temperature, 30) / 30
        moisture_factor = np.mean(self.soil_moisture) / 30
        growth = base_growth * moisture_factor
        if weather.temperature > 32:
            growth *= 0.7
        if np.mean(self.soil_moisture) < 15:
            growth *= 0.5
        self.crop_growth_stage = min(1.0, self.crop_growth_stage + growth)
        if self.crop_growth_stage >= 0.95:
            stress_factor = 1 - (max(0, weather.temperature - 30)/20)
            self.yield_kg = self.size * 5000 * stress_factor
    
    def update_pest_pressure(self, weather):
        base_growth = 0.05 * weather.temperature / 25
        humidity_factor = 1 + (weather.rainfall > 5) * 0.3
        self.pest_pressure = min(1.0, self.pest_pressure * (1 + base_growth) * humidity_factor)
        self.pest_pressure *= 0.95
    
    def decision_engine(self, sensor_data, weather):
        decisions = {
            'irrigate': False,
            'irrigation_amount': 0,
            'fertilize': False,
            'fertilizer_amount': 0,
            'apply_pesticide': False
        }
        crop_coeff = 0.3 if self.crop_growth_stage < 0.3 else (
            1.2 if self.crop_growth_stage < 0.7 else 0.6
        )
        etc = crop_coeff * weather.evapotranspiration
        deficit = max(0, 25 - sensor_data['soil_moisture_avg'])
        if deficit > 5:
            decisions['irrigate'] = True
            decisions['irrigation_amount'] = min(deficit * 1.2, 10)
        growth_stage = self.crop_growth_stage
        n_def = max(0, (40 - sensor_data['soil_N']) * growth_stage)
        if n_def > 5 and 0.2 < growth_stage < 0.8:
            decisions['fertilize'] = True
            decisions['fertilizer_amount'] = min(n_def * 2, 20)
        if sensor_data['pest_pressure'] > 0.4:
            decisions['apply_pesticide'] = True
        return decisions
    
    def execute_actions(self, decisions):
        if decisions['irrigate']:
            irrigation = decisions['irrigation_amount']
            self.soil_moisture += irrigation * 0.8
            self.irrigation_applied += irrigation
            self.water_used += irrigation
        if decisions['fertilize']:
            fertilizer = decisions['fertilizer_amount']
            self.soil_nutrients['N'] += fertilizer * 0.7
            self.fertilizer_applied += fertilizer
        if decisions['apply_pesticide']:
            self.pest_pressure *= 0.3
    
    def update_economics(self):
        self.costs['water'] += self.irrigation_applied * 0.05
        self.costs['fertilizer'] += self.fertilizer_applied * 1.2
        self.costs['labor'] += 20 / self.days
        self.costs['system'] = 3500 / (365*5)
        if self.day_counter == self.days - 1:
            self.revenue = self.yield_kg * 0.3
    
    def calculate_roi(self):
        total_cost = sum(self.costs.values()) * self.days
        net_benefit = self.revenue - total_cost
        return (net_benefit / total_cost) * 100 if total_cost > 0 else 0
    
    def generate_report(self):
        water_savings = 1 - (self.water_used / (self.size * 600))
        fertilizer_savings = 1 - (self.fertilizer_applied / (self.size * 150))
        return {
            'water_used_m3': round(self.water_used * self.size * 10, 1),
            'water_savings': round(water_savings * 100, 1),
            'fertilizer_used_kg': round(self.fertilizer_applied, 1),
            'fertilizer_savings': round(fertilizer_savings * 100, 1),
            'yield_kg': round(self.yield_kg, 1),
            'yield_increase': round((self.yield_kg / (self.size * 4000) - 1) * 100, 1),
            'total_cost': round(sum(self.costs.values()) * self.days, 2),
            'revenue': round(self.revenue, 2),
            'roi': round(self.calculate_roi(), 1),
            'sensor_uptime': round(self.sensor_network.calculate_uptime(), 1)
        }

# =============================================
# SENSOR NETWORK
# =============================================

class SensorNode:
    def __init__(self, node_id, farm, sensor_type, position):
        self.node_id = node_id
        self.farm = farm
        self.sensor_type = sensor_type
        self.position = position
        self.battery = 100
        self.operational = True
    
    def measure(self):
        if not self.operational:
            return None
        self.battery -= random.uniform(0.1, 0.5)
        if random.random() < 0.005:
            self.operational = False
            return None
        if self.sensor_type == 'soil_moisture':
            depth = int(self.position[2]*10)
            true_value = self.farm.soil_moisture[depth//10 - 1]
            noise = random.gauss(0, 0.8)
            return max(0, true_value + noise)
        elif self.sensor_type == 'nutrient':
            return max(0, self.farm.soil_nutrients['N'] + random.gauss(0, 1.2))
        elif self.sensor_type == 'pest':
            return max(0, min(100, self.farm.pest_pressure * 100 + random.gauss(0, 3)))
        return None
    
    def maintain(self):
        self.operational = True
        self.battery = 100

class SensorNetwork:
    def __init__(self, farm):
        self.farm = farm
        self.nodes = []
        self.initialize_network()
    
    def initialize_network(self):
        node_count = int(self.farm.size * 1.5)
        for i in range(node_count):
            sensor_type = ['soil_moisture', 'nutrient', 'pest'][i % 3]
            depth = random.choice([0.1, 0.3, 0.6])
            position = (
                random.uniform(0, self.farm.size ** 0.5),
                random.uniform(0, self.farm.size ** 0.5),
                depth
            )
            self.nodes.append(SensorNode(i, self.farm, sensor_type, position))
    
    def collect_data(self):
        measurements = {'soil_moisture': [], 'nutrient': [], 'pest': []}
        for node in self.nodes:
            value = node.measure()
            if value is not None:
                measurements[node.sensor_type].append(value)
            if random.random() < 0.05 and not node.operational:
                node.maintain()
        return {
            'soil_moisture_avg': np.mean(measurements['soil_moisture']) if measurements['soil_moisture'] else 0,
            'soil_moisture_var': np.var(measurements['soil_moisture']) if measurements['soil_moisture'] else 0,
            'soil_N': np.mean(measurements['nutrient']) if measurements['nutrient'] else 0,
            'pest_pressure': np.mean(measurements['pest']) / 100 if measurements['pest'] else 0
        }
    
    def calculate_uptime(self):
        return (sum(1 for node in self.nodes if node.operational) / len(self.nodes)) * 100

# =============================================
# SIMULATION EXECUTION AND VISUALIZATION
# =============================================

def run_simulation(farm_size=10, crop_type='wheat', duration=120):
    print(f"\nStarting simulation for {farm_size}ha {crop_type} farm...")
    farm = VirtualFarm(size_ha=farm_size, crop_type=crop_type, simulation_days=duration)
    daily_data = []
    while farm.advance_day():
        if farm.day_counter % 30 == 0:
            print(f"Day {farm.day_counter}: Crop at {farm.crop_growth_stage*100:.1f}% maturity")
        daily_data.append({
            'day': farm.day_counter,
            'soil_moisture': np.mean(farm.soil_moisture),
            'soil_N': farm.soil_nutrients['N'],
            'pest_pressure': farm.pest_pressure,
            'crop_growth': farm.crop_growth_stage,
            'water_used': farm.water_used,
            'irrigation': farm.irrigation_applied,
            'fertilizer': farm.fertilizer_applied
        })
    report = farm.generate_report()
    print("\n===== SIMULATION RESULTS =====")
    for k, v in report.items():
        print(f"{k}: {v}")
    plot_results(pd.DataFrame(daily_data), farm_size, crop_type)
    return report

def plot_results(data, farm_size, crop_type):
    plt.figure(figsize=(15, 10))
    plt.subplot(2, 2, 1)
    plt.plot(data['day'], data['soil_moisture'], label='Soil Moisture')
    plt.plot(data['day'], data['soil_N'], label='Soil Nitrogen')
    plt.plot(data['day'], data['crop_growth']*100, label='Crop Growth (%)')
    plt.legend(); plt.title('Soil & Crop Conditions'); plt.grid()

    plt.subplot(2, 2, 2)
    plt.plot(data['day'], data['water_used'], label='Water Used')
    plt.plot(data['day'], data['irrigation'], label='Irrigation')
    plt.bar(data['day'], data['fertilizer'], alpha=0.5, label='Fertilizer')
    plt.legend(); plt.title('Resource Use'); plt.grid()

    plt.subplot(2, 2, 3)
    plt.plot(data['day'], data['pest_pressure']*100, label='Pest Pressure')
    plt.legend(); plt.title('Pest Pressure'); plt.grid()

    plt.subplot(2, 2, 4)
    plt.scatter(data['soil_moisture'], data['crop_growth']*100, c=data['day'], cmap='viridis')
    plt.title('Growth vs Moisture'); plt.colorbar(label='Day'); plt.grid()

    plt.tight_layout()
    plt.savefig(f'agriculture_simulation_{farm_size}ha_{crop_type}.png')
    plt.show()

# =============================================
# MAIN
# =============================================

if __name__ == "__main__":
    wheat_report = run_simulation(farm_size=20, crop_type='wheat')
    tomato_report = run_simulation(farm_size=10, crop_type='tomato')
