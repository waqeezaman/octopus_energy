# main.py
from schema import BatteryConfig, EnergyProfile
from solver import EnergySolver

# Configure a 10 kWh battery with daytime charging between 06:00 and 18:00
battery_cfg = BatteryConfig(
    capacity_kwh=10.0,
    initial_soc_kwh=2.0,
    day_start_hour=6,
    day_end_hour=18
)

# Sample 24-hour time series
profile_data = EnergyProfile(
    demand=[1.5, 1.2, 1.0, 1.0, 1.2, 2.0, 3.5, 4.0, 3.0, 2.5, 2.0, 2.0, 
            2.2, 2.5, 3.0, 3.5, 4.5, 5.0, 4.0, 3.5, 2.5, 2.0, 1.8, 1.5],
    renewable=[0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 2.0, 4.5, 6.0, 7.5, 8.0, 8.0, 
               7.0, 6.0, 4.0, 2.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    grid_cost=[0.12] * 24  # $0.12 per kWh
)

# Run solver
solver = EnergySolver(battery=battery_cfg, profile=profile_data)
df_results = solver.solve()

print(df_results.head(10))