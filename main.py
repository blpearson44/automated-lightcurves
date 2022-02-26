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


CALIBRATION_PATH = "./calibrations/"

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
    try:
        df = pd.read_csv(path + "index.csv")
    except FileNotFoundError:
        print("No index file found, generating...")
        index_dir(path)
        df = pd.read_csv(path + "index.csv")
    with fits.open(input_file) as hdul:
        input_date = hdul[0].header["JD"]
        input_exposure = hdul[0].header["EXPOSURE"]

    for i in range(len(df["EXPOSURE"])):
        if not math.isclose(input_exposure, df["EXPOSURE"][i], rel_tol=0.05):
            df = df.drop(i)

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
    try:
        df = pd.read_csv(path + "index.csv")
    except FileNotFoundError:
        print("No index file found, generating...")
        index_dir(path)
        df = pd.read_csv(path + "index.csv")
    with fits.open(input_file) as hdul:
        input_date = hdul[0].header["JD"]
        input_filter = hdul[0].header["FILTER"]

    for i in range(len(df["FILTER"])):
        if df["FILTER"][i] != input_filter:
            df = df.drop(i)

    return df["FILEPATH"][closest(input_date, df["JD"])]


# TODO Manually input size of aperture
# TODO Manually input reference stars
# TODO Option for pre-calibrated files


@app.command()
def index_dir(path: str) -> None:
    """
    Index the fits files in a directory.
    Gathers:
    MJD
    ImageType (Light, Dark Frame, Flat Field)
    Exposure length
    File Path
    Presence of WCS (True/False)
    Filter type
    """
    index = {
        "MJD": [],
        "IMAGETYP": [],
        "EXPOSURE": [],
        "FILEPATH": [],
        "WCS": [],
        "FILTER": [],
    }
    for fits_file in os.scandir(path):
        if fits_file.path.endswith(".fits") or fits_file.path.endswith(".fts"):
            with fits.open(fits_file.path) as hdul:
                index["MJD"].append(hdul[0].header["JD"]) - 2400000.5
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

    Optionally manually set calibration files with --dark and --flat.
    Save data with --save and set output file with --output-file.
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
                "MJD": [date_taken - 2400000.5],
                "Magnitude": [output.magnitude],
                "Error": [output.error],
            }
        )
        if is_non_zero_file(output_file):
            df2 = pd.read_csv(output_file, index_col=0)
            df = df2.append(df, ignore_index=True)
        df.to_csv(output_file, mode="w", index=True, header=True)


@app.command()
def run_photometry_bulk(
    star_ra: float,
    star_dec: float,
    input_dir: str,
) -> None:
    """
    Run photometry on a directory. Automatically sources calibration files assuming they will be found in
    CALIBRATION_PATH/darks/dark_fits_data
    CALIBRATION_PATH/flats/flat_fits_data
    CALIBRATION_PATH is set in main.py and defaults to ./calibrations/
    """
    for input_file in os.listdir(input_dir):
        if input_file.endswith(".fits") or input_file.endswith(".fts"):
            full_path = input_dir + input_file
            run_photometry(star_ra, star_dec, full_path, save=True)


# conversion from MJD to date
def mjdtodt(mjd):
    """Return a floating point UNIX timestamp for a given MJD"""
    return [date.fromtimestamp((m - 40587) * 86400.0) for m in mjd]


def dttomjd(dttime):
    return dttime


@app.command()
def plot_lightcurve(
    input_file: str = "./Output/output.csv",
    output_file: str = "./Output/plot.png",
    title: str = "Light Curve",
) -> None:
    """
    Plot lightcurve using JD dates, magnitude, and errors.
    """
    df = pd.read_csv(input_file)
    for i in range(len(df["Error"])):
        if abs(df["Error"][i]) > 0.1:
            df = df.drop(i)
    f = plt.figure()
    f.set_figwidth(25)
    f.set_figheight(5)
    plt.scatter(df["MJD"], df["Magnitude"])
    ax = plt.gca()
    ax.invert_yaxis()
    ax.set_xlabel("MJD")
    ax.set_ylabel("Magnitude")
    ax.secondary_xaxis("top", functions=(mjdtodt, dttomjd))
    plt.errorbar(df["MJD"], df["Magnitude"], yerr=df["Error"], fmt="o")
    plt.title(title, fontsize=15, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_file)


if __name__ == "__main__":
    pho.changeSettings(
        useBiasFlag=0,
        consolePrintFlag=1,
        astrometryDotNetFlag="flyzmcwhrujaqwai",
        astrometryTimeOutFlag=100,
    )
    app()
