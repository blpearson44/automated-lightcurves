#!/usr/bin/env python3

import photometry_app as photo
import pandas as pd
import os
import logging

logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

OUTPUT_LOCATION = "./Output/"
STARS = ["RX_J2133.7+5107 (V)"]
RA_LIST = [323.4318115915129166]
DEC_LIST = [51.123536172913055]

if __name__ == "__main__":
    for i in range(len(STARS)):
        if not photo.is_non_zero_file(f"./{STARS[i]}/index.csv"):
            photo.index_dir(STARS[i])

        data = pd.read_csv(f"./{STARS[i]}/index.csv")
        logging.info(f"Performing photometry on new data points for {STARS[i]}...\n")
        for j in range(data["RAN"].size):
            if not data["RAN"][j]:
                logging.info(f'Performing photometry on {data["FILEPATH"][j]}...')
                photo.run_photometry(
                    RA_LIST[i], DEC_LIST[i], data["FILEPATH"][j], save=True
                )
                logging.info(f"Finished photometry for {data['FILEPATH'][j]}!\n")

        logging.info(
            f"Finished updating photometry for {STARS[i]}, generating light curves..."
        )
        photo.plot_lightcurve(
            f"./{OUTPUT_LOCATION}/{STARS[i]}.csv", title=f"{STARS[i]} Lightcurve"
        )
