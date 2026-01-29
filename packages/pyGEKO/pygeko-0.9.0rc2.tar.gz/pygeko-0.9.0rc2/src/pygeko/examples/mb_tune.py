"""
pyGEKO Tuning Example: Mount Bear
---------------------------------
This script demonstrates the automated model selection (tuning)
on a dataset of 87 elevation points.
"""
import time
from pygeko.kdata import Kdata
from pygeko.utils import get_data_path


def main():
    """Entry point"""
    print("--- pyGEKO Tuning Demo: Mount Bear ---")

    # 1. Load data
    montebea = get_data_path("montebea.csv")  # get path to montebea.csv
    kd = Kdata(montebea)  # read data from csv file

    # 2. Defining columns
    kd.x_col = "easting"  # which column of the dataset to use as X
    kd.y_col = "northing"  # which column of the dataset to use as Y
    kd.z_col = "heigth"  # which column of the dataset to use as Z

    print(f"Dataset loaded: {len(kd.dframe)} points.")
    print("Starting optimization scan (Multiprocessing active)...")
    start_time = time.time()

    # 3. Run the tuning scan
    # This will test 15 combinations of neighbors (nvec) and drift order (nork)
    tune_report = kd.tune(nvec_list=range(8, 17, 2), nork_list=[0, 1, 2])
    stop_time = time.time()
    print(f"Total processing time: {stop_time - start_time:.2f} seconds")

    # 4. Final summary
    print("\nOptimization finished!")

    # 5. Visualization
    print("Generating tuning heatmap...")
    kd.plot_tuning_results(tune_report)


if __name__ == "__main__":
    main()
