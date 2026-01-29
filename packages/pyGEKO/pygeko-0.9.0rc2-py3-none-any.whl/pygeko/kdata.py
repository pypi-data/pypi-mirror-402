"""
Main data handling and Kriging estimation module.
"""

import gc
import multiprocessing as mp
import os
from datetime import datetime

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import cm
from scipy.spatial import KDTree
from tqdm import tqdm

from pygeko.gplot import set_xy_axes_equal_3d
from pygeko.models import models_bool
from pygeko.utils import (
    _worker_tune,
    cross_validation,
    cross_validation_silent,
    fast_preview,
    get_octants,
    get_optimal_workers,
    report_models,
    run_full_exploration,
    run_gik,
)


class Kdata:
    """
    Manages data input and validation of generalized covariance models

    This class extends pandas dataframe with specific attributes for kriging.
    It inherits all the attributes and methods of pandas dataframe.
    """

    def __init__(self, *arg, **karg):
        """
        Kdata object creation.

        All arguments are passed to `pandas.read_csv` method, the first one
        must be a `.csv` filename containing the columns that we will use
        as X, Y, and Z values.
        """
        self.dframe = pd.read_csv(*arg, **karg)
        self.title = os.path.basename(arg[0])

        # Default column mapping
        self.x_col = "X"
        self.y_col = "Y"
        self.z_col = "Z"
        self._nork = 1
        self._nvec = 12
        self.kdtree = None
        self._scale = None  # To be initialized by self.init_neig()
        self.crossvaldata = None

    def clean_data(self, verbose: bool = True)-> int:
        """
        Removes rows containing NaN values in the active X, Y, and Z columns.
        Should be called after setting x_col, y_col, and z_col if they differ 
        from defaults.

        :param verbose: print status messages, defaults to True
        :type verbose: bool, optional
        :return: dropped rows count
        :rtype: _type_
        """        
        cols_to_check = [self.x_col, self.y_col, self.z_col]
        initial_count = len(self.dframe)
        
        # Eliminamos filas con NaNs solo en las columnas de trabajo
        self.dframe.dropna(subset=cols_to_check, inplace=True)
        
        dropped_count = initial_count - len(self.dframe)
        
        if verbose and dropped_count > 0:
            print(f"🧹 Clean-up: {dropped_count} rows containing NaNs were removed.")
        elif verbose:
            print("✅ Data is clean. No NaNs found in active columns.")
        
        return dropped_count

    @property
    def nork(self):
        """
        Polynomial order `k` getter

        :return: polynomial order `k`
        :rtype: int
        """
        return self._nork

    @nork.setter
    def nork(self, value):
        """
        Polynomial order `k` setter

        :param value: polynomial order `k`
        :type value: int
        """
        try:
            assert value in {0, 1, 2}
        except AssertionError as e:
            print(e)
            print("Oops: nork must be 1, 2 or 3 !!")
        else:
            self._nork = int(value)

    @property
    def nvec(self):
        """
        Number of neighbors to use in the calculations getter

        :return: number of neighbors
        :rtype: int
        """
        return self._nvec

    @nvec.setter
    def nvec(self, value):
        """
        Number of neighbors to use in the calculations setter

        :param value: number of neighbors
        :type value: int
        """
        try:
            assert value in range(5, 32)
        except AssertionError as e:
            print(e)
            print("Oops: nvec must be between 5 and 32 !!")
        else:
            self._nvec = int(value)

    @property
    def scale(self):
        """
        Scale factor used to stabilize the covariance matrix getter

        :return: scale factor
        :rtype: float
        """
        return self._scale

    def show(self):
        """Print the pandas dataframe"""
        print(self.dframe)

    def __getattr__(self, nombre):
        if nombre == "dframe":
            raise AttributeError(f"'{type(self).__name__}' has no 'dframe' yet.")

        try:
            return getattr(self.dframe, nombre)
        except (AttributeError, KeyError):
            raise AttributeError(
                f"'{type(self).__name__}' has no '{nombre} attribute yet.'"
            )

    @property
    def x(self):
        """
        X values getter

        :return: X values
        :rtype: numpy array
        """
        return self.dframe[self.x_col].values

    @property
    def y(self):
        """
        Y values getter

        :return: Y values
        :rtype: numpy array
        """
        return self.dframe[self.y_col].values

    @property
    def z(self):
        """
        Z values getter

        :return: Z values
        :rtype: numpy array
        """
        return self.dframe[self.z_col].values

    @property
    def status(self):
        """
        Prints information about the object
        """
        print("\nData properties:")
        print(self.dframe.describe())
        print("\nSetting:")
        print(f"x_col: {self.x_col}")
        print(f"y_col: {self.y_col}")
        print(f"z_col: {self.z_col}")
        print(f" nork: {self.nork}")
        print(f" nvec: {self.nvec}")
        print(f"Scale: {self._scale}")
        if self.crossvaldata is not None:
            print("\nCross validation data follows:")
            report_models(self)
        print("\n")

    def init_neig(self):
        """
        Initialize the KDTree for efficient spatial searching and calculate scaling factors.
        """
        # Let's make sure there are no NaNs
        self.clean_data(verbose=False)  

        self.coordinates = np.array([self.x, self.y]).T
        self.kdtree = KDTree(self.coordinates)

        # Automatic scale calculation to stabilize matrix inversion
        self.x_range = self.x.max() - self.x.min()
        self.y_range = self.y.max() - self.y.min()
        self._scale = max(self.x_range, self.y_range) / 10.0

    def findneig(self, ax, ay, n, trim=False):
        """
        Find 'n' nearest neighbors for point (ax, ay) and compute their octants.

        :param trim: If True, excludes the first match (useful for cross-validation).
        :return: Tuple (indices, distances, octants, octant_count).
        """
        if self.kdtree:
            dis, neig = self.kdtree.query([ax, ay], n + 1)

            dis = dis.flatten()
            neig = neig.flatten()

            # We calculate octants ONLY of those neighbors
            neighbor_x = self.x[neig]
            neighbor_y = self.y[neig]
            octr = get_octants(neighbor_x - ax, neighbor_y - ay)

            if trim:
                dis = dis[1:]
                neig = neig[1:]
                octr = octr[1:]
            else:
                dis = dis[:-1]
                neig = neig[:-1]
                octr = octr[:-1]

            # Number of populated octants is: len({_ for _ in octr})
            return neig, dis, octr, len({_ for _ in octr})
        else:
            raise RuntimeError("KDTree not initialized!")

    def plot(self):
        """
        2D plot of objet data
        """
        # Plot
        fig, ax = plt.subplots()

        ax.plot(self.x, self.y, "o", markersize=2, color="grey")
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("X", fontsize=10, color="darkgreen")
        ax.set_ylabel("Y", fontsize=10, color="darkgreen")
        ax.set_title(self.title, fontsize=12, fontweight="bold")
        ax.tripcolor(self.x, self.y, self.z)

        plt.show()
        plt.close("all")
        gc.collect()

    def trisurf(self, factor=1):
        """
        Plot objet data as 3D surface
        """
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        ax.plot_trisurf(
            self.x, self.y, self.z, vmin=self.z.min() * factor, cmap=cm.Blues
        )
        # ax.set_aspect("equal", adjustable="box")
        set_xy_axes_equal_3d(ax)  # X-Y axes equal scale !
        ax.set_xlabel("X", fontsize=9, color="darkgreen")
        ax.set_ylabel("Y", fontsize=9, color="darkgreen")
        ax.set_zlabel("Z", fontsize=9, color="darkgreen")
        ax.set_title(self.title, fontsize=12, fontweight="bold")
        ax.set(xticklabels=[], yticklabels=[], zticklabels=[])

        plt.show()
        plt.close("all")
        gc.collect()

    def _execute_analysis(self, preview: bool = False, verbose: bool = True):
        """
        Fit 21 generalized covariance models using generalized
        increments of order `k` and evaluates them. The results are stored
        in the `crossvaldata` attribute of the object.

        This method also initializes the object KDTree for spatial analysis.

        :param preview: Draw a quick preview of the best result as a contour map if true, defaults to False
        :type preview: bool, optional
        :param verbose: to be transmited to run_full_exploration, defaults to True
        :type verbose: bool, optional
        """
        # process = psutil.Process(os.getpid())

        if self.kdtree is None:
            self.init_neig()

        # 2. GIK Phase: Generate the increment database
        X, Y = run_gik(self, verbose=False)
        # tqdm.write(f"RAM after GIK: {process.memory_info().rss / 1024 / 1024:.2f} MB")

        # 3. GEKO Phase: Finding the best model among the 21 candidates
        res_opt, res_id, res_mae, res_rmse, res_corr = run_full_exploration(
            self, X, Y, models_bool, verbose
        )

        # We forced a physical copy of the data to break the link with the 300MB arrays
        self.zk_optimum = res_opt.copy() if hasattr(res_opt, "copy") else res_opt
        self.model_id = res_id
        self.mae = float(res_mae)
        self.rmse = float(res_rmse)
        self.corr = float(res_corr)

        # We free the local variables of the function
        del X, Y, res_opt

        # tqdm.write(f"RAM after EXPLORATION: {process.memory_info().rss / 1024 / 1024:.2f} MB")

        # 4. CROSSVAL Phase: Validate the winning model
        if verbose:
            tqdm.write("\nValidating best model...")
            actual, pred, err = cross_validation(self, self.zk_optimum)
        else:
            actual, pred, err = cross_validation_silent(self, self.zk_optimum)

        # tqdm.write(f"RAM after CROSSVAL: {process.memory_info().rss / 1024 / 1024:.2f} MB")

        # 5. FAIK Phase: Visualization and Export
        if preview:
            fast_preview(self, self.zk_optimum)

    def analyze(self, preview=False, verbose=True):
        """
        Fit 21 generalized covariance models using generalized
        increments of order `k` and evaluates them. The results are stored
        in the `crossvaldata` attribute of the object.

        This method also initializes the object KDTree for spatial analysis.

        :param preview: Draw a quick preview of the best result as a contour map if true, defaults to False
        :type preview: bool, optional
        :param verbose: to be transmited to run_full_exploration, defaults to True
        :type verbose: bool, optional
        """
        if self.kdtree is None:
            self.init_neig()
        if verbose:
            print(
                f"Executing isolated analysis (NORK={self._nork}, NVEC={self._nvec})..."
            )

        # Launch a one-time use pool
        with mp.Pool(processes=1, maxtasksperchild=1) as pool:
            res = pool.apply(_worker_tune, (self._nork, self._nvec, self, True))

        # SYNCHRONIZATION: We bring the results from the child object to the current object
        self.mae = res["mae"]
        self.rmse = res["rmse"]
        self.corr = res["corr"]
        self.model_id = res["model_id"]
        self.zk_optimum = (res["zk_optimum"],)
        self.crossvaldata = res["crossvaldata"]

        # Garbage collection
        gc.collect()
        if preview:
            fast_preview(self, self.crossvaldata[0]["zk"])
            plt.close("all")
            gc.collect()



    def save(self, verbose=True):
        """
        Save the object as a `.gck` file with metadata and a summary of the configuration for quick identification.
        """
        filename = f"{(self.title).split('.')[0]}_{self._nork}_{self._nvec}.gck"

        # 1. Extract metadata (experiment ID)
        metadata = {
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "n_puntos": len(self.dframe) if hasattr(self, "dframe") else 0,
            "params": {
                "nork": getattr(self, "nork", None),
                "nvec": getattr(self, "nvec", None),
                "model_id": getattr(self, "model_id", "Unknown"),
            },
            "metricas": {
                "MAE": getattr(self, "mae", "N/A"),
                "RMSE": getattr(self, "rmse", "N/A"),
                "Corr": getattr(self, "corr", "N/A"),
            },
        }

        # 2. Filter the payload (heavy regenerable objects)
        # We exclude kdtree and coordinates because init_neig() creates them in a second.
        payload = {
            k: v for k, v in self.__dict__.items() if k not in ["kdtree", "coordinates"]
        }

        # 3. Save the compressed package
        joblib.dump({"metadata": metadata, "payload": payload}, filename, compress=3)
        if verbose:
            tqdm.write(f"\n[OK] Saved: {filename}")
            tqdm.write(
                f"     MAE: {metadata['metricas']['MAE']} | nork: {metadata['params']['nork']} | nvec: {metadata['params']['nvec']}"
            )

    def restore(self, filename):
        """
        Load the state stored in a `.gck` fileand rebuild the spatial search engine.

        :param filename: gck filename to load
        :type filename: string
        """
        if not filename.endswith(".gck"):
            filename += ".gck"

        if not os.path.exists(filename):
            print(f"[Error] File not found: {filename}")
            return

        # Load package
        checkpoint = joblib.load(filename)
        meta = checkpoint["metadata"]

        # Restore variables to the current object
        self.__dict__.update(checkpoint["payload"])

        # CRITICAL RECONSTRUCTION
        # Since we didn't save the tree, we're rebuilding it on the fly
        self.init_neig()

        print("\n[RESTORE] Configuration recovered:")
        print(
            f"          Model: {meta['params']['model_id']} | nork: {meta['params']['nork']} | nvec: {meta['params']['nvec']}"
        )
        print(f"          Original validation: MAE={meta['metricas']['MAE']}")
        print(f"          KDTree regenerated for {meta['n_puntos']} points.")

    def tune(self, nvec_list, nork_list):
        """
        Performs an automatic parameter scan and returns the best model.

        :param nvec_list: list of integers, e.g., [8, 12, 16, 20]
        :type nvec_list: list
        :param nork_list: list of integers, defaults to [1, 2]
        :type nork_list: list, optional
        :return: list of dictionaries with tuning results
        :rtype: list
        """
        results = []
        configs = [(nork, nvec) for nork in nork_list for nvec in nvec_list]
        print(f"Starting isolated scan of {len(configs)} combinations...")

        # Configure the pool
        # maxtasksperchild=1 is the secret to total cleanup
        # processes=3 to take advantage of the RPi 5, or 1 if you want to be on the safe side
        with mp.Pool(processes=get_optimal_workers(), maxtasksperchild=1) as pool:
            # Prepare the calls
            multiple_results = [
                pool.apply_async(_worker_tune, (nk, nv, self, False)) for nk, nv in configs
            ]

            # Collect results with a progress bar
            for res in tqdm(multiple_results, desc="[TUNING SCAN]"):
                results.append(res.get())

        # Garbage collection
        gc.collect()

        # Convert to DataFrame for easier visualization
        df_tuning = pd.DataFrame(results)

        # Find the best (lowest MAE)
        best = df_tuning.loc[df_tuning["mae"].idxmin()]

        print(f"\n\n{'=' * 40}")
        print(" TUNING RESULT")
        print(f"{'=' * 40}")
        #print(df_tuning.to_string(index=False))
        print(f"Best setting: nork={best.nork}, nvec={best.nvec}")
        print(f"Minimum MAE: {best.mae:.4f} (Model #{int(best.model_id)})")
        print(f"{'=' * 40}")

        # We leave the object configured with the best parameters
        # self._execute_analysis(nork=int(best.nork), nvec=int(best.nvec))

        self._nork = int(best.nork)
        self._nvec = int(best.nvec)
        filename = f"{(self.title).split('.')[0]}_{self._nork}_{self._nvec}.gck"
        self.restore(filename)
        return df_tuning

    def plot_tuning_results(self, df_tuning):
        """Generate a static heatmap of the tuning results.

        :param df_tuning: list of dictionaries with tuning results
        :type df_tuning: list of dictionaries
        """
        pivot_table = df_tuning.pivot(index="nork", columns="nvec", values="mae")

        plt.figure(figsize=(10, 6))
        ax = sns.heatmap(
            pivot_table,
            annot=True,
            fmt=".4f",
            cmap="YlGnBu_r",
            cbar_kws={"label": "Mean Absolute Error (MAE)"},
        )

        plt.title(f"GCK Parameter Optimization: {self.title}")
        plt.xlabel("Number of Neighbors (nvec)")
        plt.ylabel("Polynomial Order (nork)")

        # temp_img = os.path.join(tempfile.gettempdir(), "gck_tuning_plot.png")
        temp_img = self.title.split(".")[0] + "_tuning.png"
        plt.savefig(temp_img, dpi=150, bbox_inches="tight")
        print(f"[PLOT] Heatmap saved to: {temp_img}")

        if os.name == "posix":
            os.system(f"xdg-open {temp_img} > /dev/null 2>&1 &")
        else:
            plt.show()
        plt.close("all")
        gc.collect()

    def __repr__(self):
            return (f"<pyGEKO.Kdata | source: '{self.title}' | "
                    f"points: {len(self.dframe)} | "
                    f"mapping: [{self.x_col}, {self.y_col}, {self.z_col}] | "
                    f"nvec: {self._nvec}, nork: {self._nork}>")