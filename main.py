"""Run photometry on target stars as a command line utility."""

# Imports
import typer
import math
import os
import pandas as pd
from datetime import date
from astropy.io import fits
import matplotlib.pyplot as plt
import photometryplus.photometry as pho


class NoFileFoundError(Exception):
    """Throw this error when a file cannot be found."""


CALIBRATION_PATH = "/Users/ben/Projects/Senior-Thesis/calibrations/"

app = typer.Typer()


def is_non_zero_file(path: str) -> bool:
    """Returns false if file is empty or does not exist, true otherwise."""
    return os.path.isfile(path) and os.path.getsize(path) > 0


def closest(num: float, sample: list) -> float:
    """Find closest value in a list."""
    return min(range(len(sample)), key=lambda i: abs(sample[i] - num))


def find_dark(input_file: str) -> str:
    """
    Find the dark file associated with a given input.

    This relies on an existing file structure of
    project
    └──main.py
    └──photometryplus/
    └──calibrations/
        └──darks/
            └──darks fits data
        └──flats/
            └──flats fits data
    """
    path = CALIBRATION_PATH + "darks/"  # default path
    dark_date = 0
    dark_exposure = 0
    input_date = 0
    input_exposure = 0
    try:
        df = pd.read_csv(path + "index.csv")
    except FileNotFoundError:
        print("No index file found, generating...")
        index_dir(path)
        df = pd.read_csv(path + "index.csv")
    with fits.open(input_file) as hdul:
        input_date = hdul[0].header["JD"]
        input_exposure = hdul[0].header["EXPOSURE"]

    return df["FILEPATH"][closest(input_date, df["JD"])]


def find_flat(input_file: str) -> str:
    """
    Find the flat file associated with a given input.

    This relies on an existing file structure of
    project
    └──main.py
    └──photometryplus/
    └──calibrations/
        └──darks/
            └──darks fits data
        └──flats/
            └──flats fits data
    """
    path = CALIBRATION_PATH + "flats/"  # default path
    flat_date = 0
    flat_exposure = 0
    input_date = 0
    input_exposure = 0
    with fits.open(input_file) as hdul:
        input_date = hdul[0].header["JD"]
        # TODO Check filter type
        # input_exposure = hdul[0].header["EXPOSURE"]

    for flat_file in os.listdir(path):
        if flat_file.endswith(".fits") or flat_file.endswith(".fts"):
            full_path = path + flat_file
            with fits.open(full_path) as hdul:
                # flat_date = hdul[0].header["JD"]
                flat_exposure = hdul[0].header["EXPOSURE"]
                if (
                    hdul[0].header["IMAGETYP"]
                    == "Flat Field"
                    # and math.isclose(flat_date, input_date, abs_tol=20)  # TODO check allowed tolerances on date for flat field
                    # and math.isclose(flat_exposure, input_exposure, abs_tol=20)  # TODO double check that exposure is not needed
                ):
                    return full_path
        else:
            pass

    raise NoFileFoundError("No flat file found.")


# TODO Manually input size of aperture
# TODO Manually input reference stars
# TODO Option for pre-calibrated files
# TODO Secondary date axis
# TODO Use error bars to determine if data points should be kept


@app.command()
def index_dir(path: str) -> None:
    """Index the fits files in a directory."""
    index = {
        "JD": [],
        "IMAGETYP": [],
        "EXPOSURE": [],
        "FILEPATH": [],
        "WCS": [],
        "FILTER": [],
    }
    for fits_file in os.scandir(path):
        if fits_file.path.endswith(".fits") or fits_file.path.endswith(".fts"):
            with fits.open(fits_file.path) as hdul:
                index["JD"].append(hdul[0].header["JD"])
                index["IMAGETYP"].append(hdul[0].header["IMAGETYP"])
                index["EXPOSURE"].append(hdul[0].header["EXPOSURE"])
                index["WCS"].append("CD1_1" in hdul[0].header)
                if "FILTER" in hdul[0].header:
                    index["FILTER"].append(hdul[0].header["FILTER"])
                else:
                    index["FILTER"].append("None")

            index["FILEPATH"].append(fits_file.path)
    df = pd.DataFrame(index)
    df.to_csv(path + "index.csv", mode="w", index=True, header=True)


@app.command()
def run_photometry(
    star_ra: float,
    star_dec: float,
    input_file: str,
    dark: str = None,
    flat: str = None,
    save: bool = False,
    output_file: str = "./Output/output.csv",
    calibrate: bool = False,
) -> None:
    """
    Run photometry on target star.
    """
    # Find calibration files if none are provided
    if dark is None:
        try:
            dark = find_dark(input_file)
        except NoFileFoundError:
            print("No dark file found.")
            return
    if flat is None:
        try:
            flat = find_flat(input_file)
        except NoFileFoundError:
            print("No flat file found.")
            return

    try:
        output = pho.runPhotometry(star_ra, star_dec, input_file, dark, "", flat)
        date_taken = ""
        with fits.open(input_file) as hdul:
            date_taken = hdul[0].header["JD"]
        pho.printReferenceToFile(
            output.referenceStars,
            "./reference-stars/" + str(round(date_taken)) + ".csv",
        )
    except AttributeError:
        print(f"File {input_file} failed.")
        return

    if save:
        df = pd.DataFrame(
            {
                "Date Taken": [date_taken],
                "Magnitude": [output.magnitude],
                "Error": [output.error],
            }
        )
        if is_non_zero_file(output_file):
            df.to_csv(output_file, mode="a", index=True, header=False)
        else:
            df.to_csv(output_file, mode="w", index=True, header=True)


@app.command()
def run_photometry_bulk(
    star_ra: float,
    star_dec: float,
    input_dir: str,
) -> None:
    """Run photometry on a directory."""
    for input_file in os.listdir(input_dir):
        if input_file.endswith(".fits") or input_file.endswith(".fts"):
            full_path = input_dir + input_file
            run_photometry(star_ra, star_dec, full_path, save=True)


@app.command()
def plot_lightcurve(
    input_file: str = "./Output/output.csv",
    output_file: str = "./Output/plot.png",
    title: str = "Light Curve",
) -> None:
    """Plot lightcurve using JD dates, magnitude, and errors."""
    df = pd.read_csv(input_file)
    for i in range(len(df["Error"])):
        if abs(df["Error"][i]) > 0.1:
            df = df.drop(i)
    plt.scatter(df["Date Taken"], df["Magnitude"])
    ax = plt.gca()
    ax.invert_yaxis()
    ax.set_xlabel("Date Taken")
    ax.set_ylabel("Magnitude")
    plt.errorbar(df["Date Taken"], df["Magnitude"], yerr=df["Error"], fmt="o")
    plt.title(title, fontsize=15, fontweight="bold")
    plt.savefig(output_file)


if __name__ == "__main__":
    pho.changeSettings(
        useBiasFlag=0,
        consolePrintFlag=1,
        astrometryDotNetFlag="flyzmcwhrujaqwai",
        astrometryTimeOutFlag=100,
    )
    app()
