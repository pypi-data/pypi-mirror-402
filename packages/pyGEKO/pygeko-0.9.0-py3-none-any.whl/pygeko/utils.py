import ctypes
import gc
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

from tqdm import tqdm

# Force NumPy to a single thread per process (must be done BEFORE importing NumPy))
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import datetime
import platform
from typing import TYPE_CHECKING, Optional, Tuple, Union  # noqa: F401

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import pdist, squareform

IS_PI = platform.machine().startswith("aarch64")

if TYPE_CHECKING:
    from pygeko.kdata import Kdata
    from pygeko.kgrid import Kgrid


def _worker_tune(nork, nvec, kd_instance, verbose):
    """
    This function runs in a separate child process.
    Upon completion, all of its memory (the 300MB leak) is lost.
    """
    kd_instance._nork = nork
    kd_instance._nvec = nvec
    kd_instance._execute_analysis(verbose=verbose)
    kd_instance.save(verbose=verbose)

    return {
        "nork": nork,
        "nvec": nvec,
        "mae": kd_instance.mae,
        "rmse": kd_instance.rmse,
        "corr": kd_instance.corr,
        "model_id": kd_instance.model_id,
        "zk_optimum": kd_instance.zk_optimum,
        "crossvaldata": getattr(kd_instance, "crossvaldata", None),
    }


def trim_memory():
    """
    On Linux systems (Raspberry Pi/Debian), this forces glibc to
    return all freed memory to the operating system.
    """
    #
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass


def get_optimal_workers() -> int:
    """
    For raspberry PI 5 leave one core free for thermal reasons

    :return: number of workers
    :rtype: int
    """
    cpus = os.cpu_count()

    return max(1, cpus - 1) if IS_PI else cpus


def _process_row(y, xi, kd_obj, zk_vec) -> list[tuple]:
    """Processes a complete row of the grid

    :param y: row Y value
    :type y: float
    :param xi: X values
    :type xi: numpy.ndarray
    :param kd_obj: Kdata object
    :type kd_obj: Kdata
    :param zk_vec: model parameters
    :type zk_vec: list[float]
    :return: estimated row
    :rtype: list[tuple]
    """
    row_results = []
    for x in xi:
        z, s = estimate_at(kd_obj, x, y, zk=zk_vec)

        # If the estimate failed, we use np.nan to maintain the gap
        if z == -999.0:
            row_results.append((x, y, np.nan, np.nan))
        else:
            row_results.append((x, y, z, s))
    return row_results


def get_octants(ax: np.ndarray, ay: np.ndarray) -> np.ndarray:
    """Determine the octant (0 to 7) for given 2D vectors (ax, ay).

    Vectorized version using NumPy to process multiple points simultaneously.

    :param ax: X values
    :type ax: np.ndarray
    :param ay: Y values
    :type ay: np.ndarray
    :return: octant array
    :rtype: np.ndarray of ints
    """
    # Convert to NumPy arrays if they are not already arrays
    ax = np.asarray(ax)
    ay = np.asarray(ay)

    # Initialize octant array
    oc = np.zeros_like(ax, dtype=int)

    # Masks for different conditions
    left = ax < 0.0  # Left semiplane
    right = ~left  # Right semiplane
    down = ay < 0.0  # Lower semiplane
    up = ~down  # Upper semiplane

    # Left semiplane
    # Third quadrant (Octants 4, 5)
    mask_45 = left & down
    # print(f"{len(mask_45) =}")
    # print(f"{len(((-ax[mask_45]) >= (-ay[mask_45]))) =}")
    oc[mask_45 & ((-ax) >= (-ay))] = 4
    oc[mask_45 & ((-ax) < (-ay))] = 5

    # Second quadrant (Octants 2, 3)
    mask_23 = left & up
    oc[mask_23 & ((-ax) >= ay)] = 3
    oc[mask_23 & ((-ax) < ay)] = 2

    # Right semiplane
    # Fourth quadrant (Octants 6, 7)
    mask_67 = right & down
    oc[mask_67 & (ax >= (-ay))] = 7
    oc[mask_67 & (ax < (-ay))] = 6

    # First quadrant (Octants 0, 1)
    mask_01 = right & up
    oc[mask_01 & (ax >= ay)] = 0
    oc[mask_01 & (ax < ay)] = 1

    return oc


def solve_linear_system(
    A: np.ndarray,
    Y: np.ndarray,
) -> tuple[int, np.ndarray]:
    """Robust solution of systems of linear equations using Least Squares.

    :param A: coefficient matrix
    :type A: np.ndarray
    :param Y: column vector
    :type Y: np.ndarray
    :return: control digit and solution
    :rtype: tuple[int, np.ndarray]
    """
    try:
        # rcond=None uses the default value based on machine precision
        solucion, residuals, rank, s = np.linalg.lstsq(A, Y, rcond=1e-15)
        return 1, solucion
    except np.linalg.LinAlgError:
        return 0, Y


def get_generalized_covariance(
    h: Union[float, np.ndarray], zk: np.ndarray
) -> Union[float, np.ndarray]:
    """Vectorized Generalized Structure Function.

    :param h: distance vector
    :type h: Union[float, np.ndarray]
    :param zk: generalized covariane function parameters
    :type zk: np.ndarray
    :return: Value(s) of the structure function (negative)
    :rtype: Union[float, np.ndarray]
    """
    h = np.asarray(h)

    # Handle case h=0
    log_h = np.zeros_like(h)
    mask = h > 0
    log_h[mask] = np.log(h[mask])
    result = zk[0] + h * zk[1] + h**3 * zk[2] + h**5 * zk[3] + (h**2 * zk[4] * log_h)

    return -result


def get_generalized_covariance_1(
    h: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """Simple linear structure function (gamma(h) = h).

    :param h: distance vector
    :type h: Union[float, np.ndarray]
    :return: Value(s) of the structure function (negative)
    :rtype: Union[float, np.ndarray]
    """
    return np.asarray(h)


def get_drift_monomial(ax: np.ndarray, ay: np.ndarray, i: int) -> np.ndarray:
    """
    Calculate vectorized 2D polynomial monomials.

    Args:
        ax: X coordinates
        ay: Y coordinates
        i: Index of the monomial (0-5)

    Returns:
        Array de valores del monomio
    """
    ax = np.asarray(ax)
    ay = np.asarray(ay)

    if i == 0:
        return np.ones_like(ax)  # Constant
    elif i == 1:
        return ax  # Linear X
    elif i == 2:
        return ay  # Linear Y
    elif i == 3:
        return ax * ax  # Quadratic X^2
    elif i == 4:
        return ay * ay  # Quadratic Y^2
    elif i == 5:
        return ax * ay  # Quadratic XY
    else:
        return np.zeros_like(ax)


def assemble_kriging_system(
    target_coords: tuple,
    neighbor_indices: np.ndarray,
    data_obj: "Kdata",
    zk: list = None,
    order: int = 1,
) -> int:
    """Assemble the matrix A and the vector b.

    :param target_coords: tuple or array (x, y) of the point to be estimated.
    :type target_coords: tuple or array
    :param neighbor_indices: the 'neig' indices returned by findneig
    :type neighbor_indices: np.ndarray
    :param data_obj: The Kdata instance (to access x, y, z)
    :type data_obj: "Kdata"
    :param zk: Vector of 5 parameters. If None, a linear structure (GIK) is used, defaults to None
    :type zk: list[float], optional
    :param order: _description_, defaults to 1
    :type order: int, optional
    :return: Drift order (0: constant, 1: linear, 2: quadratic)
    :rtype: int
    """
    n_neighbors = len(neighbor_indices)
    n_monomials = [1, 3, 6][order]  # nork=0 -> 1, nork=1 -> 3, nork=2 -> 6
    dim = n_neighbors + n_monomials

    # Extract neighbors' coordinates
    x_n = data_obj.x[neighbor_indices]
    y_n = data_obj.y[neighbor_indices]
    coords_n = np.column_stack((x_n, y_n))

    # 1. Build a Covariance Block (Neighbor Matrix)
    # We use pdist to calculate all mutual distances at once

    # SCALE FACTOR: Helps prevent h^3 and h^5 from becoming gigantic
    # You can use a fixed value based on the size of your map
    scale = data_obj.scale

    # When calculating distances, we scale:
    dist_matrix = squareform(pdist(coords_n)) / scale

    if zk is None:
        # GIK mode: gamma(h) = h
        A_cov = get_generalized_covariance_1(dist_matrix)
    else:
        # Universal Kriging Mode: gamma(h) = f(zk, h)
        A_cov = get_generalized_covariance(dist_matrix, zk)

    # 2. Constructing Drift Blocks (Monomials)
    # A[n_neighbors:, :n_neighbors] and its transpose
    M = np.zeros((n_monomials, n_neighbors))
    for i in range(n_monomials):
        M[i, :] = get_drift_monomial(x_n, y_n, i)

    # 3. Assemble Complete Matrix A
    A = np.zeros((dim, dim))
    A[:n_neighbors, :n_neighbors] = A_cov
    A[n_neighbors:, :n_neighbors] = -M  # Bottom
    A[:n_neighbors, n_neighbors:] = -M.T  # Right side (symmetry)

    # Add a tiny "nugget" to the diagonal of the covariance part
    n_neighbors = len(neighbor_indices)
    A[:n_neighbors, :n_neighbors] += np.eye(n_neighbors) * 1e-6

    # 4. Construct Vector b (Right side)
    b = np.zeros(dim)
    # Distances from the target to the neighbors
    d_target = (
        np.sqrt((x_n - target_coords[0]) ** 2 + (y_n - target_coords[1]) ** 2) / scale
    )

    if zk is None:
        b[:n_neighbors] = get_generalized_covariance_1(d_target)
    else:
        b[:n_neighbors] = get_generalized_covariance(d_target, zk)

    # Monomials at the target point
    for i in range(n_monomials):
        # We pass the coordinates directly, without wrapping them in np.array([])
        b[n_neighbors + i] = -get_drift_monomial(target_coords[0], target_coords[1], i)

    return A, b


def estimate_at(
    data_obj: "Kdata",
    ax: float,
    ay: float,
    zk: list[float] = None,
    min_octants: int = 4,
) -> tuple[float, float]:
    """Performs Kriging estimation on a coordinate (ax, ay).

    :param data_obj: Kdata object
    :type data_obj: "Kdata"
    :param ax: point X coordinate
    :type ax: float
    :param ay: point Y coordinate
    :type ay: float
    :param zk: Vector of 5 parameters. If None, a linear structure (GIK) is used, defaults to None
    :type zk: list[float], optional
    :param min_octants: minimum number of occupied octants by nvec, defaults to 4
    :type min_octants: int, optional
    :return: estimated Z and error
    :rtype: tuple[float, float]
    """

    # 1. Finding neighbors using your findneig method
    # trim=False because we are estimating at a new point (outside the data)
    nvec = data_obj.nvec
    nork = data_obj.nork
    neig, dists, octs, noct = data_obj.findneig(ax, ay, nvec, trim=False)

    # 2. Quality control: Is there sufficient angular coverage?
    if noct < min_octants:
        # If there are not enough octants, we return a null value (e.g., -999)
        return -999.0, 0.0

    # 3. Assemble the system A * x = b
    A, b = assemble_kriging_system((ax, ay), neig, data_obj, zk=zk, order=nork)

    # 4. Solve the system using solve_linear_system(lstsq)
    # weights will contain [lambda_1, ..., lambda_n, mu_1, ..., mu_m]
    success, weights = solve_linear_system(A, b)

    if not success:
        return -999.0, 0.0

    # 5. Calculate the Z* estimate = Sum(weights_i * Z_i)
    # We only use the first 'nvec' weights (the lambdas)
    lambdas = weights[: len(neig)]
    z_neighbors = data_obj.z[neig]
    z_estim = np.sum(lambdas * z_neighbors)

    # 6. Calculate the error variance: sigma^2 = Sum(weights * b)
    # In Universal Kriging, the variance is the dot product of weights and b
    sigma_sq = np.dot(weights, b)

    return z_estim, np.sqrt(max(0, sigma_sq))


def generate_grid(
    data_obj: "Kdata",
    x_range: list,
    y_range: list,
    nx: int,
    ny: int,
    zk: list[float],
    nvec: int = 12,
    nork: int = 1,
):
    """Generates a regular grid of estimates.

    :param data_obj: Kdata object
    :type data_obj: "Kdata"
    :param x_range: minimun and maximun X values
    :type x_range: list
    :param y_range: minimun and maximun Y values
    :type y_range: list
    :param nx: number of X values
    :type nx: int
    :param ny: number of Y values
    :type ny: int
    :param zk: Vector of model five parameters
    :type zk: list[float]
    :param nvec: number of neighbors to use, defaults to 12
    :type nvec: int, optional
    :param nork: polynomyal order of the drift, defaults to 1
    :type nork: int, optional
    """
    xi = np.linspace(x_range[0], x_range[1], nx)
    yi = np.linspace(y_range[0], y_range[1], ny)

    # Prepare output files
    f_val = open("faik.grd", "w")
    f_err = open("faike.grd", "w")

    print(f"Starting interpolation of {nx}x{ny} points...")

    for y in yi:
        for x in xi:
            z_estim, sigma = estimate_at(data_obj, x, y, nvec, zk=zk, nork=nork)

            # Write in X Y Z format
            f_val.write(f"{x:.3f} {y:.3f} {z_estim:.4f}\n")
            f_err.write(f"{x:.3f} {y:.3f} {sigma:.4f}\n")

        print(f"Row Y={y:.2f} completed.")

    f_val.close()
    f_err.close()
    print("Grid successfully generated")


def fast_preview(
    kd_obj: "Kdata", zk_vec: Union[list[float]], nx: int = 50, ny: int = 50
):
    """Plot a low resolution map of kriged Z and errors

    :param kd_obj: Kdata object
    :type kd_obj: "Kdata"
    :param zk_vec: Vector of model five parameters
    :type zk_vec: list[float]
    :param nx: grid size X, defaults to 50
    :type nx: int, optional
    :param ny: grid size Y, defaults to 50
    :type ny: int, optional
    """
    # 1. Define grid boundaries based on the data
    x_min, x_max = kd_obj.x.min(), kd_obj.x.max()
    y_min, y_max = kd_obj.y.min(), kd_obj.y.max()

    xi = np.linspace(x_min, x_max, nx)
    yi = np.linspace(y_min, y_max, ny)
    X, Y = np.meshgrid(xi, yi)

    Z_grid = np.zeros_like(X)
    S_grid = np.zeros_like(X)

    # 2. Grid calculation
    print(f"Interpolating {nx}x{ny} grid...")
    for i in range(ny):
        for j in range(nx):
            z, s = estimate_at(
                kd_obj,
                X[i, j],
                Y[i, j],
                zk=zk_vec,
            )
            Z_grid[i, j] = z
            S_grid[i, j] = s

    # 3. Create the figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # --- Panel 1: Estimation ---
    # We use 'terrain' or 'viridis' for relief
    im1 = ax1.contourf(X, Y, Z_grid, levels=30, cmap="terrain")
    fig.colorbar(im1, ax=ax1, label="Z Estimated")
    # Superimpose the original points to see the density.
    ax1.scatter(kd_obj.x, kd_obj.y, c="black", s=2, alpha=0.3, label="Datos")
    ax1.set_title(f"Kriged Map (nork={kd_obj.nork}, nvec={kd_obj.nvec})")
    ax1.set_xlabel(kd_obj.x_col)
    ax1.set_ylabel(kd_obj.y_col)
    ax1.set_aspect(
        "equal", adjustable="box"
    )  # We use 'equal' to maintain geographical proportions

    # --- Panel 2: Error (Uncertainty) ---
    im2 = ax2.contourf(X, Y, S_grid, levels=30, cmap="magma")
    fig.colorbar(im2, ax=ax2, label="Sigma (Error)")
    ax1.scatter(kd_obj.x, kd_obj.y, c="white", s=2, alpha=0.2)
    ax2.set_title("Standard Error Map")
    ax2.set_xlabel(kd_obj.x_col)
    ax2.set_aspect(
        "equal", adjustable="box"
    )  # We use 'equal' to maintain geographical proportions

    plt.tight_layout()
    plt.show()
    plt.close("all")
    gc.collect()




def cross_validation(
    kd_obj: "Kdata",
    zk_vec: Union[list[float]],
) -> tuple[list[float], list[float], list[float]]:
    """Perform 'Leave-One-Out' Cross Validation of models

    :param kd_obj: Kdata object
    :type kd_obj: Kdata
    :param zk_vec: Vector of model five parameters
    :type zk_vec: Union[list[float]]
    :return: _description_
    :rtype: tuple[list[float], list[float], list[float]]
    """
    nvec = kd_obj.nvec
    nork = kd_obj.nork
    n_points = len(kd_obj.x)
    actual = []
    predicted = []
    errors = []
    sigmas = []

    tqdm.write(f"Starting Cross-Validation in {n_points} points...")

    for i in range(n_points):
        tx, ty, tz = kd_obj.x[i], kd_obj.y[i], kd_obj.z[i]

        # IMPORTANT: Set trim=True to prevent itself from being used as a neighbor
        neig, dists, octs, noct = kd_obj.findneig(tx, ty, nvec, trim=True)

        if noct >= 4:  # Minimum coverage
            A, b = assemble_kriging_system(
                (tx, ty), neig, kd_obj, zk=zk_vec, order=nork
            )
            success, weights = solve_linear_system(A, b)

            if success:
                lambdas = weights[: len(neig)]
                z_est = np.sum(lambdas * kd_obj.z[neig])
                s2 = np.dot(weights, b)

                actual.append(tz)
                predicted.append(z_est)
                errors.append(tz - z_est)
                sigmas.append(np.sqrt(max(0, s2)))

    # Basic Statistics
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(np.array(errors) ** 2))
    correlation = np.corrcoef(actual, predicted)[0, 1]

    tqdm.write("\n--- CROSS-VALIDATION SUMMARY ---")
    tqdm.write(f"Validated points: {len(actual)} / {n_points}")
    tqdm.write(f"Mean Absolute Error (MAE): {mae:.4f}")
    tqdm.write(f"Root Mean Square Error (RMSE): {rmse:.4f}")
    tqdm.write(f"Correlation Coefficient: {correlation:.4f}")

    return actual, predicted, errors


def cross_validation_silent(
    kd_obj: "Kdata",
    zk_vec: Union[list[float]],
) -> tuple[list[float], list[float], list[float]]:
    """Performs silent 'Leave-One-Out' cross-validation.

    :param kd_obj: Kdata object
    :type kd_obj: Kdata
    :param zk_vec: Vector of model five parameters
    :type zk_vec: Union[list[float]]
    :return: _description_
    :rtype: tuple[list[float], list[float], list[float]]
    """
    nvec = kd_obj.nvec
    nork = kd_obj.nork
    n_points = len(kd_obj.x)
    actual = np.zeros(n_points)
    predicted = np.zeros(n_points)
    errors = np.zeros(n_points)
    # sigmas = []
    valid_idx = 0

    for i in range(n_points):
        tx, ty, tz = kd_obj.x[i], kd_obj.y[i], kd_obj.z[i]

        # IMPORTANT: Set trim=True to prevent itself from being used as a neighbor
        neig, dists, octs, noct = kd_obj.findneig(tx, ty, nvec, trim=True)

        if noct >= 4:  # Minimal coverage
            A, b = assemble_kriging_system(
                (tx, ty), neig, kd_obj, zk=zk_vec, order=nork
            )
            success, weights = solve_linear_system(A, b)

            if success:
                lambdas = weights[: len(neig)]
                z_est = np.sum(lambdas * kd_obj.z[neig])
                # s2 = np.dot(weights, b)

                actual[valid_idx] = tz
                predicted[valid_idx] = z_est
                errors[valid_idx] = tz - z_est
                valid_idx += 1
                # sigmas.append(np.sqrt(max(0, s2)))

    return actual[:valid_idx], predicted[:valid_idx], errors[:valid_idx]


def export_grid(
    kg_obj: "Kgrid",
    zk_vec: Union[list[float], np.ndarray],
    filename: str = "RESULTADO",
    res_x: int = 100,
    res_y: int = 100,
):
    """
    Generate a grid and export it to a CSV file (X, Y, Z, Sigma). Multithreaded version.

    :param kg_obj: Kgrid object
    :type kg_obj: Kgrid
    :param zk_vec: Vector of model five parameters
    :type zk_vec: Union[list[float], np.ndarray]
    :param filename: filename base, defaults to "RESULTADO"
    :type filename: str, optional
    :param res_x: grid size X, defaults to 100
    :type res_x: int, optional
    :param res_y: grid size Y, defaults to 100
    :type res_y: int, optional
    """
    x_min, x_max = kg_obj.xmin, kg_obj.xmax
    y_min, y_max = kg_obj.ymin, kg_obj.ymax

    xi = np.linspace(x_min, x_max, res_x)
    yi = np.linspace(y_min, y_max, res_y)

    filename1 = filename + ".grd"
    filename2 = filename + ".hdr"
    print(f"Exporting {res_x}x{res_y} grid in parallel to {filename1}...")

    # We use ProcessPoolExecutor to distribute the rows among the cores
    all_results = []
    # with ProcessPoolExecutor(max_workers=4) as executor:
    with ProcessPoolExecutor(max_workers=get_optimal_workers()) as executor:
        # We map the function to each value of y (row)
        futures = {
            executor.submit(_process_row, y, xi, kg_obj.kdata, zk_vec): y for y in yi
        }
        # 2. Usamos as_completed para capturar resultados según terminen
        for future in tqdm(as_completed(futures), total=len(futures), desc="Kriging"):
            row_index = futures[future]
            try:
                all_results.extend(future.result())
                # Guardar el resultado en tu matriz...
            except Exception as e:
                print(f"Error en fila {row_index}: {e}")

    # Save results
    with open(filename1, "w") as f:
        f.write("X,Y,Z_ESTIM,SIGMA\n")
        for res in all_results:
            f.write(f"{res[0]:.3f},{res[1]:.3f},{res[2]:.4f},{res[3]:.4f}\n")

    print(f"Export completed. Now writing metadata to {filename2}...")
    with open(filename2, "w") as f:
        f.write("type: GRID\n")
        f.write(f"file: {kg_obj.kdata.title}\n")
        f.write(f"x_col: {kg_obj.kdata.x_col}\n")
        f.write(f"y_col: {kg_obj.kdata.y_col}\n")
        f.write(f"z_col: {kg_obj.kdata.z_col}\n")
        f.write(f"ntot: {kg_obj.kdata.shape[0]}\n")
        f.write(f"nork: {kg_obj.kdata.nork}\n")
        f.write(f"nvec: {kg_obj.kdata.nvec}\n")
        f.write(f"model: {kg_obj.model}\n")
        f.write(f"zk: {zk_vec}\n")
        f.write(f"xmin: {x_min}\n")
        f.write(f"xmax: {x_max}\n")
        f.write(f"ymin: {y_min}\n")
        f.write(f"ymax: {y_max}\n")
        f.write(f"bins: {res_x}\n")
        f.write(f"hist: {res_y}\n")
        f.write(f"date: {datetime.datetime.now()}\n")

    print("Completed.")

    print(f"Completed. Data saved to {filename1}")


def run_gik(kd_obj: "Kdata", verbose) -> Tuple[np.ndarray, np.ndarray]:
    """Generate the generalized increment database

    :param kd_obj: Kdata object
    :type kd_obj: "Kdata"
    :param verbose: print banner, defaults to True
    :return: X: Contribution matrix (N_increments, 5), Y: Vector of squared increments (N_increments)
    :rtype: tuple[np.ndarray, np.ndarray]
    """
    nvec = kd_obj.nvec
    nork = kd_obj.nork
    n_points = len(kd_obj.x)
    contributions = []
    squared_increments = []

    if verbose:
        tqdm.write(f"Generating GIK's for {n_points} data points...")

    for i in range(n_points):
        tx, ty, tz = kd_obj.x[i], kd_obj.y[i], kd_obj.z[i]

        # 1. Find neighbors (using trim=True to create the increment)
        neig, _, _, noct = kd_obj.findneig(tx, ty, nvec, trim=True)

        if noct < 4:
            continue

        # 2. Obtain GIK weights using gamma(h) = h (Fixed linear structure)
        # This gives us the lambda weights that filter out drift
        A, b = assemble_kriging_system((tx, ty), neig, kd_obj, zk=None, order=nork)
        success, weights = solve_linear_system(A, b)

        if not success:
            continue

        # We are only interested in the lambdas (the first one is the one at the center point, -1)
        lambdas = weights[: len(neig)]
        # The increment is: I = Z_target - Sum(lambda_j * Z_j)
        # Or in general: I = Sum(w_j * Z_j) where w_target = 1 and w_j = -lambda_j
        w = np.concatenate([[-1.0], lambdas])
        indices = np.concatenate([[i], neig])

        # Value of the squared increment
        inc_val = (tz - np.sum(lambdas * kd_obj.z[neig])) ** 2

        # 3. Calculate the contribution of each basis f_k(h) to this increment
        # C_k = Sum_a Sum_b (w_a * w_b * f_k(dist_ab))
        coords = np.column_stack((kd_obj.x[indices], kd_obj.y[indices]))
        from scipy.spatial.distance import pdist, squareform

        dists = squareform(pdist(coords))

        c_k = np.zeros(5)
        # f0=1, f1=h, f2=h^3, f3=h^5, f4=h^2*log(h)
        # We use the utils functions in vectorized form
        c_k[0] = np.sum(np.outer(w, w) * 1.0)
        c_k[1] = np.sum(np.outer(w, w) * dists)
        c_k[2] = np.sum(np.outer(w, w) * dists**3)
        c_k[3] = np.sum(np.outer(w, w) * dists**5)

        # f4 with log(0) handling
        d2 = dists**2
        log_d = np.zeros_like(dists)
        mask = dists > 0
        log_d[mask] = np.log(dists[mask])
        c_k[4] = np.sum(np.outer(w, w) * d2 * log_d)

        contributions.append(c_k)
        squared_increments.append(inc_val)

    return np.array(contributions), np.array(squared_increments)


def run_geko(
    X: np.ndarray, Y: np.ndarray, models_array: np.ndarray[bool]
) -> np.ndarray[float]:
    """Try all 22 models and return the best one.

    :param X: Contribution matrix (N_increments, 5)
    :type X: np.ndarray
    :param Y: Vector of squared increments (N_increments)
    :type Y: np.ndarray
    :param models_array: model structure array
    :type models_array: np.ndarray[bool]
    :return: best model parameters
    :rtype: np.ndarray[float]
    """
    best_error = float("inf")
    best_zk = None
    best_model_idx = -1

    tqdm.write(f"\nExploring {len(models_array)} structure models...")

    for idx, mask in enumerate(models_array):
        mask = mask.astype(bool)
        # Select only the active columns of the current model
        X_sub = X[:, mask]

        # Solve the overdetermined system: X_sub * zk_sub = Y
        # We use lstsq to obtain the best least-squares solution
        success, zk_sub = solve_linear_system(X_sub, Y)

        if success:
            # Reconstruct the 5-element vector zk
            zk_full = np.zeros(5)
            zk_full[mask] = zk_sub

            # Calculate residual error (ECM)
            error = np.mean((np.dot(X_sub, zk_sub) - Y) ** 2)

            # In GCK, must zk[1] be negative to represent covariance?
            # (It depends on the convention, but here we're looking for the smallest residual error)
            if error < best_error:
                best_error = error
                best_zk = zk_full
                best_model_idx = idx

    tqdm.write(f"Optimization complete! Best model: #{best_model_idx}")
    tqdm.write(f"ZK Optimum: {best_zk}")
    return best_zk


def run_full_exploration(
    kd_obj: "Kdata",
    X_gik: np.ndarray,
    Y_gik: np,
    models_array: np.ndarray[bool],
    verbose: bool = True,
) -> tuple[np.ndarray[float], int, float, float, float]:
    """Test all 22 models, perform cross-validation for each one and save the results to kd_obj.crossvaldata

    :param kd_obj: Kdata object
    :type kd_obj: "Kdata"
    :param X_gik: Contribution matrix (N_increments, 5)
    :type X_gik: np.ndarray
    :param Y_gik: Vector of squared increments (N_increments)
    :type Y_gik: np.ndarray
    :param models_array: model structure array
    :type models_array: np.ndarray[bool]
    :param verbose: print results for each model, defaults to True
    :return: best model parameters
    :rtype: tuple[np.ndarray[float], int, float, float, float]
    """

    del kd_obj.crossvaldata
    gc.collect()
    kd_obj.crossvaldata = []  # List to save results

    if verbose:
        tqdm.write(
            f"{'Mod':<4} | {'MAE':<10} | {'RMSE':<10} | {'Corr':<8} | {'Status'}"
        )
        tqdm.write("-" * 50)

    for idx, mask in enumerate(models_array):
        # 1. GIK adjustment (Least squares to obtain zk)
        mask_bool = mask.astype(bool)
        success, zk_sub = solve_linear_system(X_gik[:, mask_bool], Y_gik)

        if success:
            zk_full = np.zeros(5)
            zk_full[mask_bool] = zk_sub

            # 2. Cross-validation for this specific model
            # (We calculate real metrics to compare models)
            actual, pred, errs = cross_validation_silent(kd_obj, zk_full)

            if len(actual) > 0:
                mae = np.mean(np.abs(errs))
                rmse = np.sqrt(np.mean(np.array(errs) ** 2))
                corr = np.corrcoef(actual, pred)[0, 1]

                # 3. Save to history
                res = {
                    "model_idx": idx,
                    "mask": mask.copy(),  # Copia explícita
                    "zk": zk_full.copy(),  # <--- MUY IMPORTANTE: copia física del array
                    "mae": float(mae),  # Asegurar que son tipos nativos
                    "rmse": float(rmse),
                    "corr": float(corr),
                    "success": True,
                }
                kd_obj.crossvaldata.append(res)

                if verbose:
                    tqdm.write(
                        f"{idx:<4} | {mae:<10.4f} | {rmse:<10.4f} | {corr:<8.4f} | OK"
                    )
            else:
                if verbose:
                    tqdm.write(f"{idx:<4} | {'-':<10} | {'-':<10} | {'-':<8} | CV fail")
        else:
            if verbose:
                tqdm.write(
                    f"{idx:<4} | {'-':<10} | {'-':<10} | {'-':<8} | Matrix error"
                )

    # Sort by RMSE to suggest the best one at the end
    kd_obj.crossvaldata.sort(key=lambda x: x["rmse"])

    return (
        kd_obj.crossvaldata[0]["zk"],
        kd_obj.crossvaldata[0]["model_idx"],
        kd_obj.crossvaldata[0]["mae"],
        kd_obj.crossvaldata[0]["rmse"],
        kd_obj.crossvaldata[0]["corr"],
    )


def report_models(kd_obj):
    """Print a detailed report of all tested models.

    :param kd_obj: Kdata object
    :type kd_obj: "Kdata"
    """
    if not hasattr(kd_obj, "crossvaldata") or not kd_obj.crossvaldata:
        print("There is no validation data. Run .analize() first.")
        return

    # Sort by RMSE (best at the top)
    sorted_models = sorted(kd_obj.crossvaldata, key=lambda x: x["rmse"])

    print(
        f"\n{'RANK':<5} | {'MOD':<4} | {'MAE':<10} | {'RMSE':<10} | {'CORR':<8} | {'ZK (Coefficients)'}"
    )
    print("-" * 100)

    for rank, res in enumerate(sorted_models, 1):
        zk_str = "[" + " ".join([f"{v:8.2e}" for v in res["zk"]]) + "]"
        star = "★" if rank == 1 else " "
        print(
            f"{star} {rank:<3} | {res['model_idx']:<4} | {res['mae']:<10.4f} | {res['rmse']:<10.4f} | {res['corr']:<8.4f} | {zk_str}"
        )

    print("-" * 100)
    print(f"Best model is #{sorted_models[0]['model_idx']}.")


def get_data_path(filename: str) -> str:
    """Gets the absolute path to a file in the package's data folder.

    :param filename: file to load
    :type filename: str
    :return: path to CSV test file
    :rtype: str
    """
    from importlib import resources

    path = resources.files("pygeko").joinpath("testdata").joinpath(filename)
    return str(path)
