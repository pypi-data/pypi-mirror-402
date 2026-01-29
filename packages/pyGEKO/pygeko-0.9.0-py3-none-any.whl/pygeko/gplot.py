"""GRID plotting"""

import gc
import os
import tempfile
import webbrowser

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from matplotlib import cm  # noqa: F401


def set_xy_axes_equal_3d(ax: plt.Axes):
    """
    Adjust the 3D axis limits of a graph so that the aspect ratio is
    'equal' ONLY for the X and Y axes, leaving the Z axis free.

    :param ax: plt.Axes object
    :type ax: plt.Axes
    """
    x_lim = ax.get_xlim3d()
    y_lim = ax.get_ylim3d()

    x_range = abs(x_lim[1] - x_lim[0])
    x_middle = np.mean(x_lim)
    y_range = abs(y_lim[1] - y_lim[0])
    y_middle = np.mean(y_lim)

    # 1. Find the largest range only between X and Y
    plot_radius = 0.5 * max([x_range, y_range])

    # 2. Establecer los límites de X e Y usando este rango
    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])

    # 3. **IMPORTANT:** The Z-axis limits remain unchanged


class Gplot:
    """
    Plotting methods for grids
    """

    def __init__(self, fnamebase: str):
        """
        Class constructor

        :param fnamebase: `grd` and `hdr` filename base
        :type fnamebase: str
        """
        self.title = os.path.basename(fnamebase)

        # Load grid data
        self.grid_df = pd.read_csv(fnamebase + ".grd")

        # Load metadata
        self.meta = {}
        try:
            with open(fnamebase + ".hdr", "r") as f:
                for line in f:
                    if ":" in line:
                        key, val = line.strip().split(": ", 1)
                        self.meta[key] = val
        except FileNotFoundError:
            print(f"Warning: Metadata file not found {fnamebase}.hdr")

        # Extract dimensions and prepare 2D arrays for plotting
        # We use the column names defined in the exporter
        self.nx = int(self.meta.get("bins", 100))
        self.ny = int(self.meta.get("hist", 100))

        # Reshape de los datos (X, Y, Z, Sigma)
        self.X = self.grid_df["X"].values.reshape(self.ny, self.nx)
        self.Y = self.grid_df["Y"].values.reshape(self.ny, self.nx)
        self.Z = self.grid_df["Z_ESTIM"].values.reshape(self.ny, self.nx)
        self.E = self.grid_df["SIGMA"].values.reshape(self.ny, self.nx)

    @property
    def metadata(self):
        """
        Print grid metadata
        """
        print("\nGrid metadata:")
        for _ in self.meta:
            print("    ", _, "=", self.meta[_])

    def _format_coord(self, x: np.array, y: np.array) -> str:
        """
        Internal function to display Z values ​​when moving the cursor

        :param x: X array
        :type x: np.array
        :param y: Y array
        :type y: np.array
        :return: formated string
        :rtype: str
        """
        # Find the nearest index in the grid
        ix = np.argmin(np.abs(self.X[0, :] - x))
        iy = np.argmin(np.abs(self.Y[:, 0] - y))
        z_val = self.Z[iy, ix]
        e_val = self.E[iy, ix]
        return f"X={x:.2f}, Y={y:.2f} | Z={z_val:.2f}, Err={e_val:.2f}"

    def contourc(
        self,
        v_min: float = None,
        v_max: float = None,
        bad: str = "red",
    ):
        """
        Plot an interactive map of estimated Z and its errors with a continuous color map

        :param v_min: minimum Z value to map, defaults to None
        :type v_min: float, optional
        :param v_max: maximum Z value to map, defaults to None
        :type v_max: float, optional
        :param bad: bad pixels color, defaults to "red"
        :type bad: str, optional
        """
        Z_plot = self.Z.copy()
        # print(f"{v_min=}, {v_max=}, {np.nanmin(self.Z)=}, {np.nanmax(self.Z)=}, ")
        if v_min is None:
            v_min = np.nanmin(self.Z)
        if v_max is None:
            v_max = np.nanmax(self.Z)
        # self.Z = np.clip(self.Z, v_min, v_max)
        # print(f"{v_min=}, {v_max=}, {np.nanmin(self.Z)=}, {np.nanmax(self.Z)=}, ")
        Z_plot[Z_plot < v_min] = np.nan

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), sharex=True, sharey=True)

        # 1. Configure color map for Z (Relief)
        cmap_z = cm.terrain.copy()
        cmap_z.set_bad(color=bad)  # Bad pixels in RED

        # 2. Configure color map for Error (Deep Sky)
        cmap_e = cm.inferno.copy()
        cmap_e.set_bad(color="white")  # Bad pixels in WHITE

        # Draw Z Estimate
        # print(v_min, v_max)
        im1 = ax1.imshow(
            Z_plot,
            extent=[self.X.min(), self.X.max(), self.Y.min(), self.Y.max()],
            origin="lower",
            cmap=cmap_z,
            aspect="equal",
            vmin=v_min,
            vmax=v_max,
        )
        ax1.set_title("Estimated Z")
        fig.colorbar(im1, ax=ax1, label="Estimated Z")

        # Draw Standard Error
        im2 = ax2.imshow(
            self.E,
            extent=[self.X.min(), self.X.max(), self.Y.min(), self.Y.max()],
            origin="lower",
            cmap=cmap_e,
        )
        ax2.set_title("Error")
        fig.colorbar(im2, ax=ax2, label="Error")

        plt.tight_layout()
        plt.show()
        plt.close("all")
        gc.collect()

    def contourd(
        self,
        v_min: float = None,
        v_max: float = None,
        nlevels: int = 25,
    ):
        """
        Plot an interactive map of estimated Z and its errors with a discrete color map

        :param v_min: minimum Z value to map, defaults to None
        :type v_min: float, optional
        :param v_max: maximum Z value to map, defaults to None
        :type v_max: float, optional
        :param nlevels: number of levels, defaults to 25
        :type nlevels: int, optional
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), sharex=True, sharey=True)

        if v_min is None:
            v_min = np.nanmin(self.Z)
        if v_max is None:
            v_max = np.nanmax(self.Z)

        # Draw Z Estimate
        # Panel 1: Z estimated
        # Generate exactly 25 slices between v_min and v_max
        levels_cuts = np.linspace(v_min, v_max, nlevels)

        c1 = ax1.contourf(
            self.X,
            self.Y,
            self.Z,
            levels=levels_cuts,
            cmap="terrain",
            vmin=v_min,
            vmax=v_max,
            # extend="both"
        )
        fig.colorbar(c1, ax=ax1, label="Estimated Z")
        ax1.set_title("Estimated Z")
        ax1.set_aspect("equal")

        # Panel 2: Error (Sigma)
        c2 = ax2.contourf(self.X, self.Y, self.E, levels=nlevels, cmap="magma")
        fig.colorbar(c2, ax=ax2, label="Error")
        ax2.set_title("Error")
        ax2.set_aspect("equal")

        # Interactivity: Display values ​​in the status bar
        ax1.format_coord = self._format_coord
        ax2.format_coord = self._format_coord

        plt.tight_layout()
        plt.show()
        plt.close("all")
        gc.collect()

    def zsurf(self):
        """
        3D surface of the estimated Z
        """
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection="3d")
        surf = ax.plot_surface(
            self.X, self.Y, self.Z, cmap="terrain", edgecolor="none", antialiased=True
        )
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
        set_xy_axes_equal_3d(ax)  # X-Y axes equal scale !
        ax.set_title("Kriged " + self.meta["z_col"] + " " + self.title)
        ax.set_zlabel(self.meta["z_col"])
        ax.set_xlabel(self.meta["x_col"])
        ax.set_ylabel(self.meta["y_col"])
        # Force equal scaling in X-Y (limited in Matplotlib 3D, but it helps)
        ax.set_aspect("auto")
        plt.show()
        plt.close("all")
        gc.collect()

    def esurf(self):
        """
        3D surface of the estimated Z errors
        """
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection="3d")
        surf = ax.plot_surface(
            self.X, self.Y, self.E, cmap="magma", edgecolor="none", antialiased=True
        )
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
        set_xy_axes_equal_3d(ax)  # X-Y axes equal scale !
        ax.set_title("Standard Error " + self.title)
        ax.set_xlabel(self.meta["x_col"])
        ax.set_ylabel(self.meta["y_col"])

        plt.show()
        plt.close("all")
        gc.collect()

    def zsurf_gpu(
        self,
        z_floor: float = None,
        v_exag: float = 0.5,
        cmap: str = "earth",
        contours: bool = False,
    ):
        """
        Smooth rendering using WebGL and your GPU

        :param z_floor: plot only above this value, defaults to None
        :type z_floor: float, optional
        :param v_exag: vertical exageration factor, defaults to 0.5
        :type v_exag: float, optional
        :param cmap: plotly color map name, defaults to "earth"
        :type cmap: str, optional
        :param contours: add contours, defaults to False
        :type contours: bool, optional

        """
        # Optional: To make the surface "die" at the ground instead of sinking
        # Z_plot = self.Z.copy()
        # Z_plot[Z_plot < z_floor] = np.nan # NaNs in Plotly create gaps or clean cuts
        if z_floor is None:
            z_floor = np.nanmin(self.Z)
        fig = go.Figure(
            data=[go.Surface(z=self.Z, x=self.X, y=self.Y, colorscale=cmap)]
        )
        range_x = self.X.max() - self.X.min()
        range_y = self.Y.max() - self.Y.min()
        if contours:
            fig.update_traces(
                contours_z=dict(
                    show=True,
                    usecolormap=True,
                    highlightcolor="limegreen",
                    project_z=True,
                )
            )
        fig.update_layout(
            title="Estimated Z 3D (GPU Accelerated)",
            autosize=True,
            scene=dict(
                zaxis=dict(range=[z_floor, np.nanmax(self.Z) * 1.2]),
                aspectratio=dict(x=1, y=range_y / range_x, z=v_exag),
            ),
        )
        fig.show()
        gc.collect()
        # return fig

    def zsurf_gpu_PI(
        self,
        z_floor: float = None,
        v_exag: float = 0.5,
        cmap: str = "earth",
        contours: bool = False,
    ):
        """
        Renders the 3D surface using WebGL and opens it in the system's browser.
        Optimized for remote VNC sessions and Raspberry Pi 5.

        :param z_floor: plot only above this value, defaults to None
        :type z_floor: float, optional
        :param v_exag: vertical exageration factor, defaults to 0.5
        :type v_exag: float, optional
        :param cmap: plotly color map name, defaults to "earth"
        :type cmap: str, optional
        :param contours: add contours, defaults to False
        :type contours: bool, optional
        """

        if z_floor is None:
            z_floor = np.nanmin(self.Z)
        # 1. Generate the figure
        fig = go.Figure(
            data=[go.Surface(z=self.Z, x=self.X, y=self.Y, colorscale=cmap)]
        )
        range_x = self.X.max() - self.X.min()
        range_y = self.Y.max() - self.Y.min()

        if contours:
            fig.update_traces(
                contours_z=dict(
                    show=True,
                    usecolormap=True,
                    highlightcolor="limegreen",
                    project_z=True,
                )
            )
        fig.update_layout(
            title="Estimated Z 3D (GPU Accelerated)",
            autosize=True,
            scene=dict(
                zaxis=dict(range=[z_floor, np.nanmax(self.Z) * 1.2]),
                aspectratio=dict(x=1, y=range_y / range_x, z=v_exag),
            ),
        )

        # 2. Define path in temporary directory
        # We use tempfile to make it cross-platform (i7 and Pi)
        temp_file = os.path.join(tempfile.gettempdir(), "gck_3d_view.html")

        # 3. Export toa HTML
        fig.write_html(
            temp_file,
            auto_open=False,
            include_plotlyjs="cdn",
            post_script="window.dispatchEvent(new Event('resize'));",
        )

        # 4. Non-blocking opening according to the Operating System
        print("[GPU-VIEW] Opening viewer in browser...")

        try:
            if os.name == "posix":  # Linux (Debian on i7 and Pi)
                # xdg-open sends the file to the default browser and releases the terminal
                os.system(f"xdg-open {temp_file} > /dev/null 2>&1 &")
            else:
                # Windows option
                webbrowser.open(f"file://{os.path.realpath(temp_file)}")

        except Exception as e:
            print(f"Error trying to open the browser: {e}")
            print(f"You can open the file manually in: {temp_file}")

    def save_zsurf(
        self,
        filename: str = None,
        z_floor: float = None,
        v_exag: float = 0.5,
        cmap: str = "earth",
        contours: bool = False,
    ):
        """Export the interactive 3D model to a separate HTML file.

        :param filename: filename, defaults to self.title + "_3d_model"
        :type filename: str, optional
        :param z_floor: plot only above this value, defaults to None
        :type z_floor: float, optional
        :param v_exag: vertical exageration factor, defaults to 0.5
        :type v_exag: float, optional
        :param cmap: plotly color map name, defaults to "earth"
        :type cmap: str, optional
        :param contours: add contours, defaults to False
        :type contours: bool, optional
        """

        if filename is None:
            filename = self.title + "_3d_model"
        if z_floor is None:
            z_floor = np.nanmin(self.Z)

        # 1. Create the figure (same logic as zsurf_gpu)
        range_x = self.X.max() - self.X.min()
        range_y = self.Y.max() - self.Y.min()

        fig = go.Figure(
            data=[
                go.Surface(
                    z=self.Z,
                    x=self.X,
                    y=self.Y,
                    colorscale=cmap,
                    lighting=dict(
                        ambient=0.4, diffuse=0.5, roughness=0.9, specular=0.1
                    ),
                    colorbar=dict(title="Estimated Z"),
                )
            ]
        )

        if contours:
            fig.update_traces(
                contours_z=dict(
                    show=True,
                    usecolormap=True,
                    highlightcolor="limegreen",
                    project_z=True,
                )
            )
        fig.update_layout(
            title="Estimated Z - Interactive 3D Model",
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title="Z",
                zaxis=dict(range=[z_floor, np.nanmax(self.Z) * 1.2]),
                aspectratio=dict(x=1, y=range_y / range_x, z=v_exag),
            ),
            margin=dict(l=0, r=0, b=0, t=40),
        )

        # 2. Save as HTML
        output_file = f"{filename}.html"
        fig.write_html(output_file)
        print(f"3D model successfully exported to: {output_file}")

    def __repr__(self):
        # Verificamos si hay datos cargados para evitar errores si el grid está vacío
        status = "Ready" if self.Z is not None else "Empty (No grid estimated)"
        shape = f"{self.Z.shape}" if self.Z is not None else "N/A"

        return (
            f"<pyGEKO.Gplot | Status: {status} | "
            f"Grid Shape: {shape} | "
            f"Source: '{self.title}'>"
        )
