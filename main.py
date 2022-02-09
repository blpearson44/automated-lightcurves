"""Run photometry on target stars as a command line utility."""

# Imports
import typer
import pandas as pd
from datetime import date
from astropy.io import fits
import photometryplus.photometry as pho


# star_RA = 323.4318115915129166
# star_DEC = 51.123536172913055
# # input_file = "/Users/ben/projects/Senior-Thesis/test.fts"
# input_file = "/Users/ben/projects/Senior-Thesis/RX_J2133.7+5107 (V)/RX_J2133.7+5107 V-20200505at082302_-25-1X1-300-V.fts"
# dark = "/Users/ben/projects/Senior-Thesis/calibrations/darks/master_dark_20211007_1X1_300.fits"
# flats = "/Users/ben/projects/Senior-Thesis/calibrations/flats/master_flat_20210722_1X1_V.fits"

app = typer.Typer()


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
    dark = ""
    dark_date = 0
    dark_exposure = 0
    input_date = 0
    input_exposure = 0
    with fits.open(input_file) as hdul:
        input_date = hdul[0].header["JD"]  # TODO cal type
        input_exposure = hdul[0].header["EXPOSURE"]

    return dark


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
    flat = ""
    return flat


# TODO Manually input size of pixels
# TODO Manually input reference stars
# TODO Option for pre-calibrated files


@app.command()
def run_photometry(
    star_ra: float,
    star_dec: float,
    input_file: str,
    dark: str = None,
    flat: str = None,
    save: bool = False,
    output_file: str = "./Output/output.csv",
) -> None:
    """Run photometry on target star."""
    if dark is None:
        find_dark(input_file)
    if flat is None:
        find_flat(input_file)
    output = pho.runPhotometry(star_ra, star_dec, input_file, dark, "", flat)
    pho.printReferenceToFile(
        output.referenceStars, "./reference-stars/" +
        str(date.today()) + ".csv"
    )
    if save:
        date_taken = ""
        with fits.open(input_file) as hdul:
            date_taken = hdul[0].header["JD"]
        df = pd.DataFrame(
            {
                "Date Added": [date.today()],
                "Date Taken": [date_taken],
                "magnitude": [output.magnitude],
                "error": [output.error],
            }
        )
        df.to_csv(output_file, mode="a", index=False, header=False)


pho.changeSettings(useBiasFlag=0)

if __name__ == "__main__":
    app()
