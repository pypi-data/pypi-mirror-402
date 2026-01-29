import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image


def generate_test_data(
    png_path: str,
    n_samples: int=1000,
    output_csv: str=None,
    visualize: bool=True,
    invert_y: bool=False,
    seed:int=None,
):
    """Read a 16-bit PNG DEM, extract N random points and export to CSV.

    :param png_path: path to PNG with DEM data
    :type png_path: str
    :param n_samples: number of data points to sample, defaults to 1000
    :type n_samples: int, optional
    :param output_csv: output CSV filename, defaults to None
    :type output_csv: str, optional
    :param visualize: preview sample points on PNG, defaults to True
    :type visualize: bool, optional
    :param invert_y: adapt Y axis to respect geografical orientation, defaults to False
    :type invert_y: bool, optional
    :param seed: _descseed to make results reproducible, defaults to None
    :type seed: int, optional
    """
    if output_csv is None:
        output_csv = os.path.splitext(png_path)[0] + f"_n{n_samples}.csv"

    try:
        # Open image and ensure 16-bit reading
        img = Image.open(png_path)
        img_data = np.asarray(img, dtype=np.uint16)
    except Exception as e:
        print(f"Error: The image could not be opened or processed.'{png_path}'. {e}")
        return

    height, width = img_data.shape[:2]
    print(f"\n--- Processing: {png_path} ---")
    print(
        f"Resolution: {width}x{height} | Z range: [{img_data.min()}, {img_data.max()}]"
    )

    # Configure generator with seed for reproducibility
    rng = np.random.default_rng(seed)

    # Random sampling
    x_coords = rng.integers(0, width, size=n_samples)
    y_coords = rng.integers(0, height, size=n_samples)

    # Extract Z values ​​(NumPy uses [row, column])
    z_values = img_data[y_coords, x_coords]

    # Adjusting Y Coordinates (Topographic vs. Image)
    # In the image, 0,0 is top-left. On the map, 0,0 is bottom-left.
    y_final = (height - 1) - y_coords if invert_y else y_coords

    df = pd.DataFrame(
        {
            "X": x_coords.astype(float),
            "Y": y_final.astype(float),
            "Z": z_values.astype(float),
        }
    )

    df.to_csv(output_csv, index=False)
    print(f"Success: {n_samples} points stored in'{output_csv}'")
    if seed:
        print(f"Using seed: {seed}")

    if visualize:
        plt.figure(figsize=(8, 8))
        # We adjust the origin of the graph according to the chosen convention.
        origin = "lower" if invert_y else "upper"
        plt.imshow(img_data, cmap="gray", origin=origin)

        # If we invert Y, the points for the scatter plot should be consistent with the plot
        plt.scatter(
            x_coords,
            y_coords if not invert_y else (height - 1) - y_coords,
            c="red",
            s=3,
            alpha=0.6,
            label="Sample Points",
        )

        plt.title(f"Sampling: {n_samples} points (Y-Invert: {invert_y})")
        plt.xlabel("X (Píxels)")
        plt.ylabel("Y (Píxels)")
        plt.legend()
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Random sample generator for pyGEKO from 16-bit PNG DEMs."
    )

    # Argumento posicional
    parser.add_argument("input", help="Path to the PNG DEM file.")

    # Argumentos opcionales
    parser.add_argument(
        "-n",
        "--samples",
        type=int,
        default=1000,
        help="Number of random samples to generate, defaults to 1000.",
    )

    parser.add_argument("-o", "--output", help="Output CSV filename.")

    parser.add_argument(
        "-s", "--seed", type=int, help="Random seed for reproducibility."
    )

    parser.add_argument(
        "--no-viz", action="store_true", help="Turn off the display of sample points."
    )

    parser.add_argument(
        "--invert-y",
        action="store_true",
        help="Invert the Y axis to match geographical orientation.",
    )

    args = parser.parse_args()

    generate_test_data(
        png_path=args.input,
        n_samples=args.samples,
        output_csv=args.output,
        visualize=not args.no_viz,
        invert_y=args.invert_y,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
