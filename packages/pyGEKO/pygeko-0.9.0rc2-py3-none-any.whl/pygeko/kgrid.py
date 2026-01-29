"""
pyGEKO Kgrid Module
-------------------
Handles grid definition and Kriging estimation.
"""

from pygeko.kdata import Kdata
from pygeko.utils import (
    export_grid,
    fast_preview,
    report_models,
)


class Kgrid:
    """Manages grid definitions and interpolation workflow."""

    def __init__(self, kdata, xmin, xmax, ymin, ymax, bins, hist):
        """
        Class constructor

        :param kdata: _description_
        :type kdata: _type_
        :param xmin: _description_
        :type xmin: _type_
        :param xmax: _description_
        :type xmax: _type_
        :param ymin: _description_
        :type ymin: _type_
        :param ymax: _description_
        :type ymax: _type_
        :param bins: _description_
        :type bins: _type_
        :param hist: _description_
        :type hist: _type_
        """
        assert isinstance(kdata, Kdata)
        self.kdata = kdata
        # Estimation window parameters
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        # Grid resolution
        self.bins = bins  # X axis
        self.hist = hist  # Y axis
        # Model
        self._model = None
        self.zk_final = None

    @property
    def status(self):
        """
        Print the status of the object
        """
        print(f"Data from: {self.kdata.title}")
        print("Columns")
        print(f"x_col = {self.kdata.x_col}")
        print(f"y_col = {self.kdata.y_col}")
        print(f"z_col = {self.kdata.z_col}")
        print("Window:")
        print(f"xmin = {self.xmin}")
        print(f"xmax = {self.xmax}")
        print(f"ymin = {self.ymin}")
        print(f"ymax = {self.ymax}")
        print("Grid:")
        print(f"bins = {self.bins}")
        print(f"hist = {self.hist}")
        if self.model:
            print(f"Model = {self.model}")
            print(f"   zk = {self.zk_final} ")

    @property
    def models(self):
        """
        Print a detailed report of all tested models.
        """
        report_models(self.kdata)

    @property
    def model(self):
        """
        Selected model getter
        """
        return self._model

    @model.setter
    def model(self, value):
        """
        Selected model setter

        :param value: model to set
        :type value: int
        """
        self._model = value
        final_model = next(
            m for m in self.kdata.crossvaldata if m["model_idx"] == value
        )
        self.zk_final = final_model["zk"]

    def ask_model(self):
        """
        Method to ask interactivel for the model to use for the final map.
        """
        self._model = int(
            input("\nEnter the model number (MOD) you want to use for the final map: ")
        )

        final_model = next(
            m for m in self.kdata.crossvaldata if m["model_idx"] == self._model
        )
        self.zk_final = final_model["zk"]

    def estimate_grid(self, preview=False, filename="result"):
        """
        Run the grid estimation using the parent Kdata model.

        :param preview: plot a contour map preview if True, defaults to False
        :type preview: bool, optional
        :param filename: grid result filename base, defaults to "result"
        :type filename: str, optional
        """
        print(f"\n[GRID] Generating map with Model #{self.model}...")
        if preview:
            fast_preview(self.kdata, self.zk_final)
        export_grid(
            self,
            self.zk_final,
            filename=f"{filename}_{self.kdata.nork}_{self.kdata.nvec}_mod_{self.model}",
            res_x=self.bins,
            res_y=self.hist,
        )

    def __repr__(self):
            # Determinamos si el modelo ha sido ajustado
            model_str = f"| Model: {self.model}" if self.model else "| Model: Not fitted"
            
            # Construimos una cadena informativa de varias líneas o una sola compacta
            return (
                f"<pyGEKO.Kgrid | Source: '{self.kdata.title}'\n"
                f"  Window: x[{self.xmin}, {self.xmax}], y[{self.ymin}, {self.ymax}]\n"
                f"  Grid: bins={self.bins}, hist={self.hist} {model_str} >"
            )