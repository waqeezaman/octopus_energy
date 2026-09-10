# solver.py
import pandas as pd
from ortools.linear_solver import pywraplp
from schema import BatteryConfig, EnergyProfile


class EnergySolver:
    def __init__(self, battery: BatteryConfig, profile: EnergyProfile):
        self.battery = battery
        self.profile = profile
        self.T = range(len(profile.demand))

    def solve(self) -> pd.DataFrame:
        # Create the Google OR-Tools Linear Solver using the GLOP engine
        solver = pywraplp.Solver.CreateSolver("GLOP")
        if not solver:
            raise RuntimeError("Google OR-Tools GLOP solver is unavailable.")

        infinity = solver.infinity()

        # Decision Variables
        E = [solver.NumVar(0.0, infinity, f"Grid_Import_{t}") for t in self.T]
        B = [solver.NumVar(0.0, self.battery.capacity_kwh, f"SoC_{t}") for t in self.T]
        B_in = [solver.NumVar(0.0, infinity, f"Charge_{t}") for t in self.T]
        B_out = [solver.NumVar(0.0, infinity, f"Discharge_{t}") for t in self.T]
        W = [solver.NumVar(0.0, infinity, f"Waste_{t}") for t in self.T]

        # Constraints
        for t in self.T:
            # 1. Energy balance constraint: Supply == Demand
            solver.Add(
                self.profile.renewable[t] + E[t] + B_out[t]
                == self.profile.demand[t] + B_in[t] + W[t]
            )
            

            # 3. Battery storage continuity equation
            prev_soc = self.battery.initial_soc_kwh if t == 0 else B[t - 1]
            solver.Add(B[t] == prev_soc + B_in[t] - B_out[t])

        # Objective Function: Minimize total cost of grid imports
        objective = solver.Objective()
        for t in self.T:
            objective.SetCoefficient(E[t], self.profile.grid_cost[t])
        objective.SetMinimization()

        # Solve the model
        status = solver.Solve()

        if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
            raise ValueError("No feasible solution found for the energy schedule.")

        # Extract results into a Pandas DataFrame
        return pd.DataFrame({
            "Demand": self.profile.demand,
            "Renewable": self.profile.renewable,
            "Grid_Import": [E[t].solution_value() for t in self.T],
            "Battery_SoC": [B[t].solution_value() for t in self.T],
            "Charge": [B_in[t].solution_value() for t in self.T],
            "Discharge": [B_out[t].solution_value() for t in self.T],
            "Wasted_Renewable": [W[t].solution_value() for t in self.T],
        })