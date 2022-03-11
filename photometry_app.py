"""Run photometry on target stars as a command line utility."""
# TODO Manually input size of aperture
# TODO Manually input reference stars
# TODO Option for pre-calibrated files

# Imports
import os
import math
import logging
import warnings
from datetime import date
import typer
import pandas as pd
from astropy.io import fits
from astropy.wcs import FITSFixedWarning
import matplotlib.pyplot as plt
import photometryplus.photometry as pho

warnings.filterwarnings("ignore", category=FITSFixedWarning, append=True)


pho.changeSettings(
    useBiasFlag=0,
    consolePrintFlag=0,
    astrometryDotNetFlag="flyzmcwhrujaqwai",
    astrometryTimeOutFlag=100,
)


class NoFileFoundError(Exception):
    """Throw this error when a file cannot be found."""


CALIBRATION_PATH = "./calibrations/"
OUTPUT_DIR = "./Output/"

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
        logging.info("No index file found, generating...")
        index_dir(path)
        df = pd.read_csv(path + "index.csv")
    with fits.open(input_file) as hdul:
        input_date = hdul[0].header["JD"] - 2400000.5
        input_exposure = hdul[0].header["EXPOSURE"]

    for i in range(len(df["EXPOSURE"])):
        if not math.isclose(input_exposure, df["EXPOSURE"][i], rel_tol=0.05):
            df = df.drop(i)

    return df["FILEPATH"][closest(input_date, df["MJD"])]


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
        logging.info("No index file found, generating...")
        index_dir(path)
        df = pd.read_csv(path + "index.csv")
    with fits.open(input_file) as hdul:
        input_date = hdul[0].header["JD"] - 2400000.5
        input_filter = hdul[0].header["FILTER"]

    for i in range(len(df["FILTER"])):
        if df["FILTER"][i] != input_filter:
            df = df.drop(i)

    return df["FILEPATH"][closest(input_date, df["MJD"])]


@app.command()
def index_dir(path: str, clean_run: bool = False) -> None:
    """
    Index the fits files in a directory.
    Flags: clean-run, generates new index file from scratch
    Gathers:
    MJD
    ImageType (Light, Dark Frame, Flat Field)
    Exposure length
    File Path
    Presence of WCS (True/False)
    Filter type
    Whether or not file has already been run
    """
    index = {
        "MJD": [],
        "IMAGETYP": [],
        "EXPOSURE": [],
        "FILEPATH": [],
        "WCS": [],
        "FILTER": [],
        "RAN": [],
    }
    index_file = f"{path}/index.csv"
    index_info = {}
    if is_non_zero_file(index_file) and not clean_run:
        index_info = pd.read_csv(index_file)
        index_files = []
        for fits_file in index_info["FILEPATH"]:
            index_files.append(
                f"{fits_file}"
            )  # this really shouldn't be necessary but the filepath doesn't match up unless I make a new list
    for fits_file in os.scandir(path):
        if fits_file.path.endswith(".fits") or fits_file.path.endswith(".fts"):
            if not clean_run:
                if fits_file.path in index_files:
                    logging.info("Skipping %s", fits_file.path)
                    pass
                else:
                    logging.info(
                        "File %s not found in index, generating...", fits_file.path
                    )
            with fits.open(fits_file.path) as hdul:
                index["MJD"].append(hdul[0].header["JD"] - 2400000.5)
                index["IMAGETYP"].append(hdul[0].header["IMAGETYP"])
                index["EXPOSURE"].append(hdul[0].header["EXPOSURE"])
                index["WCS"].append("CD1_1" in hdul[0].header)
                if "FILTER" in hdul[0].header:
                    index["FILTER"].append(hdul[0].header["FILTER"])
                else:
                    index["FILTER"].append("None")

            index["FILEPATH"].append(fits_file.path)
            index["RAN"].append(False)
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
    output_file: str = None,
    calibrate: bool = False,
) -> None:
    """
    Run photometry on target star.

    Optionally manually set calibration files with --dark and --flat.
    Save data with --save and set output file with --output-file.
    """
    # Find calibration files if none are provided
    index_file = f"{os.path.dirname(input_file)}/index.csv"
    if not is_non_zero_file(index_file):
        index_dir(os.path.dirname(input_file))
    if output_file is None:
        try:
            with fits.open(input_file) as hdul:
                output_file = f'{OUTPUT_DIR}{hdul[0].header["OBJECT"]}.csv'
        except KeyError:
            logging.info(
                "Error: No Object keyword found in input_file, using output.csv..."
            )
            output_file = f"{OUTPUT_DIR}output.csv"
    if dark is None:
        try:
            dark = find_dark(input_file)
            logging.info("Closest dark file is %s", dark)
        except NoFileFoundError:
            logging.error("No dark file found.")
            return
    if flat is None:
        try:
            flat = find_flat(input_file)
            logging.info("Closest flat file is %s", flat)
        except NoFileFoundError:
            logging.error("No flat file found.")
            return

    if not find_in_csv(index_file, input_file, "WCS"):
        logging.info(
            "Need to generate WCS data for %s, this may take a few minutes...",
            input_file,
        )
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
        logging.error(
            "AttributeError: File %s failed (usually because reference stars could not be found).",
            input_file,
        )
        return

    if save:
        data_out = pd.DataFrame(
            {
                "MJD": [date_taken - 2400000.5],
                "Magnitude": [output.magnitude],
                "Error": [output.error],
            }
        )
        if is_non_zero_file(output_file):
            data_out2 = pd.read_csv(output_file, index_col=0)
            data_out = data_out2.append(data_out, ignore_index=True)
        data_out.to_csv(output_file, mode="w", index=True, header=True)
        # tell index file that this file has been run
        if is_non_zero_file(index_file):
            index_df = find_in_csv(index_file, input_file, "RAN", True)
            index_df.to_csv(index_file, mode="w", index=True, header=True)
        else:
            logging.info("No index file found.")


def find_in_csv(index_file: str, path: str, column: str, cell_value=None):
    """Find a file from it's path in a csv, make a change to it and return dataframe or don't make a change and return value at collumn."""
    df = pd.read_csv(index_file, index_col=0)
    for i in range(df["FILEPATH"].size):
        if os.path.abspath(path) == os.path.abspath(f'./{df["FILEPATH"][i]}'):
            if cell_value is None:
                return df[column][i]
            else:
                df.at[i, column] = cell_value
                return df
    raise NoFileFoundError(f"Filepath {path} not found in index csv {index_file}.")


# TODO flag for whether or not to rerun files?
@app.command()
def run_photometry_bulk(
    star_ra: float,
    star_dec: float,
    input_dir: str,
    run_on_wcs: bool = False,
    run_all: bool = False,
) -> None:
    """
    Run photometry on a directory. Automatically sources calibration files assuming they will be found in
    CALIBRATION_PATH/darks/dark_fits_data
    CALIBRATION_PATH/flats/flat_fits_data
    CALIBRATION_PATH is set in main.py and defaults to ./calibrations/
    """
    index_file = f"./{input_dir}index.csv"
    if not is_non_zero_file(index_file) and not run_on_wcs:
        logging.info("No index file found, generating...")
        index_dir(input_dir, clean_run=True)
        logging.info("Success! Beginning photometry on %s", input_dir)
    for input_file in os.listdir(input_dir):
        full_path = input_dir + input_file
        if input_file.endswith(".fits") or input_file.endswith(".fts"):
            try:
                wcs = find_in_csv(index_file, full_path, "WCS")
            except NoFileFoundError:
                logging.info("%s not found in index", input_file)
                continue
            if run_on_wcs or wcs:
                if run_all or not find_in_csv(index_file, full_path, "RAN"):
                    logging.info("Performing photometry on %s...", input_file)
                    run_photometry(star_ra, star_dec, full_path, save=True)
                    logging.info("Success!")
                else:
                    logging.info("File %s already ran previously, skipping", input_file)
            else:
                logging.info("No WCS data for %s, skipping.", input_file)


# conversion from MJD to date
def mjdtodt(mjd):
    """Return a floating point UNIX timestamp for a given MJD"""
    return [date.fromtimestamp((m - 40587) * 86400.0) for m in mjd]


def dttomjd(dttime):
    return dttime


@app.command()
def plot_lightcurve(
    input_file: str = "output.csv",
    output_file: str = None,
    title: str = None,
) -> None:
    """
    Plot lightcurve using JD dates, magnitude, and errors.
    """
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".png"
    if title is None:
        title = os.path.splitext(input_file)[0]
    df = pd.read_csv(input_file)
    for i in range(len(df["Error"])):
        if abs(df["Error"][i]) > 0.1:
            df = df.drop(i)
    data = df.to_dict("list")
    f = plt.figure()
    f.set_figwidth(25)
    f.set_figheight(5)
    ax = plt.gca()
    ax.invert_yaxis()
    final_index = data["MJD"].index(max(data["MJD"]))
    final_mjd, final_mag, final_error = (
        data["MJD"].pop(final_index),
        data["Magnitude"].pop(final_index),
        data["Error"].pop(final_index),
    )
    ax.set_xlabel("MJD")
    ax.set_ylabel("Magnitude")
    ax.secondary_xaxis("top", functions=(mjdtodt, dttomjd))
    plt.errorbar(
        data["MJD"],
        data["Magnitude"],
        yerr=data["Error"],
        fmt="o",
        color="blue",
    )
    plt.errorbar(
        final_mjd,
        final_mag,
        yerr=final_error,
        fmt="o",
        color="red",
    )
    plt.title(title, fontsize=15, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_file)


if __name__ == "__main__":
    app()
