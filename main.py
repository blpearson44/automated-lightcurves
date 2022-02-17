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

    pass


CALIBRATION_PATH = "/Users/ben/Projects/Senior-Thesis/calibrations/"

app = typer.Typer()


def is_non_zero_file(path: str) -> bool:
    """Returns false if file is empty or does not exist, true otherwise."""
    return os.path.isfile(path) and os.path.getsize(path) > 0


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
    with fits.open(input_file) as hdul:
        # input_date = hdul[0].header["JD"]  # TODO check allowed tolerances with date
        #
        input_exposure = hdul[0].header["EXPOSURE"]

    for dark_file in os.listdir(path):
        if dark_file.endswith(".fits") or dark_file.endswith(".fts"):
            full_path = path + dark_file
            with fits.open(full_path) as hdul:
                # dark_date = hdul[0].header["JD"]
                dark_exposure = hdul[0].header["EXPOSURE"]
                if (
                    hdul[0].header["IMAGETYP"] == "Dark Frame"
                    # and math.isclose(dark_date, input_date, abs_tol=20)
                    and math.isclose(
                        dark_exposure, input_exposure, abs_tol=20
                    )  # TODO check allowed tolerances with exposure time
                ):
                    return full_path
        else:
            pass

    raise NoFileFoundError("No dark file found.")


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


@app.command()
def index_dir(path: str) -> None:
    """Index the fits files in a directory."""
    index = {"JD": [], "IMAGETYP": [], "EXPOSURE": []}
    for fits_file in os.scandir(path):
        if fits_file.path.endswith(".fits") or fits_file.path.endswith(".fts"):
            with fits.open(fits_file.path) as hdul:
                index["JD"].append(hdul[0].header["JD"])
                index["IMAGETYP"].append(hdul[0].header["IMAGETYP"])
                index["EXPOSURE"].append(hdul[0].header["EXPOSURE"])
    df = pd.DataFrame(index)
    df.to_csv(path + "index.csv", mode="w", index=False, header=True)


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
            df.to_csv(output_file, mode="a", index=False, header=False)
        else:
            df.to_csv(output_file, mode="w", index=False, header=True)


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
