"""pyGEKO Kdata.save basic test"""

from pygeko.kdata import Kdata
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

    kd.analyze(preview=False)  # Generalized covariance analysis and cross-validation
    kd.save()                  # Save results to `.gck` file
    
if __name__ == '__main__':
    main()

