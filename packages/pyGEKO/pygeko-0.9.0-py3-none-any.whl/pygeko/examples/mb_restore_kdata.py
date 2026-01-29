"""pyGEKO Kdata.restore basic test

First, you need to run `mb_save_kdata.py`
"""

from pygeko import Kdata, Kgrid
from pygeko.utils import get_data_path
from pygeko import Gplot

def main():
    """Entry point"""
    # Load and analyze data
    montebea = get_data_path("montebea.csv")  # get path to montebea.csv
    kd = Kdata(montebea)                      # read data from csv file


    kd.restore("montebea_1_14")               # restore state from saved `.gck` file
    kd.status                                 # verify...

    kg = Kgrid(kd, 0.0, 1000.0, 0.0, 1400.0, 500, 700)   # define estimation window and grid resolution
    kg.model = 20   # for batch or script use
    kg.estimate_grid(filename="montebea", preview=False) # let's go...

    gp=Gplot("montebea_1_14_mod_20")          # create Gplot object
    gp.contourd()                             # Plot contours map with discrete colormap

if __name__ == '__main__':

    main()

