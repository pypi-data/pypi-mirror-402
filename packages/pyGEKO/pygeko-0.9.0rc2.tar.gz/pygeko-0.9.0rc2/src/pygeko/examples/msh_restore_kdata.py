"""pyGEKO Kdata.restore basic test

First, you need to run `msh_save_kdata.py`
"""

from pygeko import Kdata, Kgrid
from pygeko.utils import get_data_path
from pygeko import Gplot

def main():
    """Entry point"""
    # Load and analyze data
    msh5000 = get_data_path("msh5000.csv")  # get path to msh5000.csv
    kd = Kdata(msh5000)                      # read data from csv file
    # The next line ensures that Z is within the same order of magnitude as X and Y. 
    # This improves the conditioning of the Kriging matrix, which is vital on 
    # limited hardware like the RPi 5.
    kd.Z /= 60.0  # Normalized for numerical stability

    kd.restore("msh5000_1_20")               # restore state from saved `.gck` file
    kd.status                                 # verify...

    kg = Kgrid(kd, 0.0, 1024.0, 0.0, 1024.0, 1000, 1000)   # define estimation window and grid resolution
    kg.model = 13   # for batch or script use
    kg.estimate_grid(filename="msh5000", preview=False) # let's go...

    gp=Gplot("msh5000_1_20_mod_13")          # create Gplot object
    gp.contourd()                             # Plot contours map with discrete colormap

if __name__ == "__main__":

    main()
