"""pyGEKO Kdata.save basic test"""

from pygeko.kdata import Kdata
from pygeko.utils import get_data_path


def main():
    """Entry point"""
    # Load and analyze data
    msh5000 = get_data_path("msh5000.csv")  # get path to msh5000.csv
    kd = Kdata(msh5000)                      # read data from csv file
    # The next line ensures that Z is within the same order of magnitude as X and Y. 
    # This improves the conditioning of the Kriging matrix, which is vital on 
    # limited hardware like the RPi 5.
    kd.Z /= 60.0  # Normalized for numerical stability
    
    #  defining parameters
    kd.nork = 1             # order of generalized increments to use
    kd.nvec = 20            # number of nearest neighbors to use

    # data analysis

    kd.analyze(preview=False)  # Generalized covariance analysis and cross-validation
    kd.save()                  # Save results to `.gck` file

if __name__ == "__main__":

    main()
