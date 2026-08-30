import numpy as np
from scipy.interpolate import RegularGridInterpolator
import pandas as pd

class GeoModBenchmarkHarness:
    """
    Test harness for simulating standard dataset reads from the GeoMod Consortium.
    Used for benchmarking GRAIN 2.0 results against established literature.
    """
    def __init__(self, benchmark_name="GeoMod 2008 Thrust Wedge Benchmark"):
        self.benchmark_name = benchmark_name
        self.reference_data = None
        self.reference_grid_x = None
        self.reference_grid_y = None

    def load_reference_data(self, filepath=None):
        """
        Mocks loading a reference matrix from literature.
        If filepath is provided, it can be extended to load real CSV/NPZ data.
        """
        if filepath is None:
            print(f"[*] Simulating load of reference data for '{self.benchmark_name}'...")
            # Create a coarse grid typical of literature data (e.g., 20x10)
            self.reference_grid_x = np.linspace(0, 100, 20)
            self.reference_grid_y = np.linspace(0, 50, 10)
            
            X, Y = np.meshgrid(self.reference_grid_x, self.reference_grid_y)
            # Mock displacement field (coarse)
            self.reference_data = np.sin(X / 20.0) * np.cos(Y / 10.0) * 10.0
            print(f"    -> Loaded coarse reference grid: {self.reference_data.shape}")
        else:
            print(f"[*] Loading actual reference data from {filepath}...")
            # Placeholder for actual data loading logic
            # e.g., self.reference_data = np.loadtxt(filepath, delimiter=',')
            pass

    def interpolate_to_grain_grid(self, grain_x, grain_y):
        """
        Performs spatial interpolation to match the coarse GeoMod grid
        with the high-resolution grid of GRAIN 2.0.
        """
        if self.reference_data is None:
            raise ValueError("Reference data not loaded. Call load_reference_data() first.")

        print(f"[*] Interpolating coarse GeoMod grid to GRAIN 2.0 high-res grid ({len(grain_y)}x{len(grain_x)})...")
        
        # Scipy RegularGridInterpolator setup
        # Note: reference_grid_y corresponds to rows, reference_grid_x corresponds to columns
        interp = RegularGridInterpolator(
            (self.reference_grid_y, self.reference_grid_x), 
            self.reference_data, 
            bounds_error=False, 
            fill_value=np.nan
        )
        
        GRAIN_X, GRAIN_Y = np.meshgrid(grain_x, grain_y)
        
        # Stack coordinates for interpolation
        pts = np.vstack((GRAIN_Y.ravel(), GRAIN_X.ravel())).T
        interpolated_ref = interp(pts).reshape(GRAIN_Y.shape)
        
        return interpolated_ref

    def calculate_rmse(self, grain_data, interpolated_reference):
        """
        Calculates the Root Mean Square Error (RMSE) between GRAIN 2.0 calculations
        and the interpolated GeoMod reference data.
        """
        squared_errors = (grain_data - interpolated_reference) ** 2
        mse = np.nanmean(squared_errors)
        rmse = np.sqrt(mse)
        return rmse

    def run_comparison(self, grain_x, grain_y, grain_data):
        """
        Executes the comparison workflow and prints the evaluation metrics table.
        """
        interpolated_ref = self.interpolate_to_grain_grid(grain_x, grain_y)
        rmse = self.calculate_rmse(grain_data, interpolated_ref)
        mae = np.nanmean(np.abs(grain_data - interpolated_ref))
        max_err = np.nanmax(np.abs(grain_data - interpolated_ref))
        
        print("\n" + "="*60)
        print(f" COMPARISON RESULTS: GRAIN 2.0 vs {self.benchmark_name}")
        print("="*60)
        
        metrics_df = pd.DataFrame({
            "Evaluation Metric": [
                "Root Mean Square Error (RMSE)", 
                "Mean Absolute Error (MAE)", 
                "Max Absolute Error"
            ],
            "Value": [
                f"{rmse:.4f}", 
                f"{mae:.4f}", 
                f"{max_err:.4f}"
            ],
            "Unit": ["mm/s", "mm/s", "mm/s"]  # Assuming velocity/displacement unit
        })
        
        print(metrics_df.to_string(index=False))
        print("="*60 + "\n")
        
        return metrics_df

def main():
    print("=== GeoMod Benchmark Harness Initialization ===")
    harness = GeoModBenchmarkHarness()
    
    # 1. Simulate loading reference matrix from literature
    harness.load_reference_data()
    
    # 2. Simulate GRAIN 2.0 high-resolution calculations
    print("[*] Generating mock GRAIN 2.0 high-resolution calculated data...")
    grain_x = np.linspace(0, 100, 200)  # High res X (200 pts)
    grain_y = np.linspace(0, 50, 100)   # High res Y (100 pts)
    GRAIN_X, GRAIN_Y = np.meshgrid(grain_x, grain_y)
    
    # Mocking GRAIN data with some noise and slight deviation from the ideal reference
    ideal_highres = np.sin(GRAIN_X / 20.0) * np.cos(GRAIN_Y / 10.0) * 10.0
    noise = np.random.normal(0, 0.25, ideal_highres.shape)
    grain_calculated_data = ideal_highres * 1.05 + noise # 5% bias + noise
    
    # 3 & 4. Interpolate and print RMSE comparison table
    harness.run_comparison(grain_x, grain_y, grain_calculated_data)

if __name__ == "__main__":
    main()
