"""pyGEKO workflow basic test"""

import time
import gc
from pygeko.kdata import Kdata
from pygeko.kgrid import Kgrid
from pygeko import Gplot
from pygeko.utils import get_data_path

def main():
    """Entry point"""
    # Load and analyze data
    montebea = get_data_path("montebea.csv")  # get path to montebea.csv
    kd = Kdata(montebea)                      # read data from csv file

    #  defining parameters
    kd.x_col = "easting"    # which column of the dataset to use as X
    kd.y_col = "northing"   # which column of the dataset to use as Y
    kd.z_col = "heigth"     # which column of the dataset to use as Z
    kd.nork = 1             # order of generalized increments to use
    kd.nvec = 14            # number of nearest neighbors to use

    # data analysis
    start = time.time()
    kd.analyze(preview=False)  # Generalized covariance analysis and cross-validation
    stop = time.time()
    print(f"analyze() took: {stop - start} seconds")

    # Create kriging object with estimation window and grid definition
    kg = Kgrid(kd, 0.0, 1000.0, 0.0, 1400.0, 500, 700)   # define estimation window and grid resolution
    #kg.models       # inspect models to choose answer to the following .ask_model() call
    #kg.ask_model() # for interactivve use
    kg.model = 20   # for batch or script use
    #kg.status       # an inspection of problem definitions

    kg.estimate_grid(filename="montebea", preview=True) # let's go...

    # Garbage collection
    gc.collect()

    # Let us see the result
    gp=Gplot("montebea_1_14_mod_20")          # create Gplot object
    gp.contourd()                             # Plot contours map with discrete colormap

if __name__ == '__main__':

    main()

