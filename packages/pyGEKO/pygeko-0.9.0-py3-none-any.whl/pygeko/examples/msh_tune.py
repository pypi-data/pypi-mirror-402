"""
pyGEKO Tuning Example: Mount St. Helens
---------------------------------------
This script demonstrates the automated model selection (tuning)
on a dataset of 5,000 elevation points.
"""

import gc
import time

from pygeko.kdata import Kdata
from pygeko.utils import get_data_path


def main():
    print("--- pyGEKO Tuning Demo: Mount St. Helens ---")
    print("     --- This will take a while... ---")

    # 1. Load data
    msh_path = get_data_path("msh5000.csv")
    kd = Kdata(msh_path)

    # 2. Scale Z values
    # We scale Z to match the X,Y range (approx. 0-1000) to improve
    # the numerical stability of the Kriging system (GIK).
    kd.Z /= 60.0

    print(f"Dataset loaded: {len(kd.dframe)} points.")
    print("Starting optimization scan (Multiprocessing active)...")

    # 3. Run the tuning scan
    # This will test 30 combinations of neighbors (nvec) and drift order (nork)
    start_time = time.time()
    tune_report = kd.tune(nvec_list=range(14, 33, 2), nork_list=[0, 1, 2])
    stop_time = time.time()
    
    # 4. Final summary
    print("\nOptimization finished!")
    print(f"Total processing time: {stop_time - start_time:.2f} seconds")

    # 5. Visualization
    print("Generating tuning heatmap...")
    kd.plot_tuning_results(tune_report)

    # Garbage collection
    gc.collect()


if __name__ == "__main__":
    main()
