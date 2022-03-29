#!/usr/bin/env python3
"""Primary script to check over data for updates."""

import os
import shutil
import logging
import pandas as pd
import photometry_app as photo

logging.basicConfig(
    format="%(levelname)s: %(asctime)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)

OUTPUT_LOCATION = "./Output/"
STAR_DIR = "/datadrive/gbo/rawdata/shaw_ip_monitoring/"
sources = pd.read_csv("./Stars_List.csv")
sources = sources.to_dict("list")
stars = sources["Source_name"]
ra_list = sources["RA"]
dec_list = sources["Dec"]

if __name__ == "__main__":
    for i in range(len(stars)):
        object_dir = f"{STAR_DIR}{stars[i]}"
        if not os.path.isdir(f"{object_dir}/"):
            logging.error("./%s/ does not exist, skipping star observations.", stars[i])
            continue
        if not photo.is_non_zero_file(f"{object_dir}/index.csv"):
            photo.index_dir(f"{object_dir}/", clean_run=True)

        data = pd.read_csv(f"{object_dir}/index.csv")
        logging.info("Performing photometry on new data points for %s...\n", stars[i])
        for j in range(data["RAN"].size):
            if not data["RAN"][j] and data["WCS"][j]:
                logging.info("Performing photometry on %s...", data["FILEPATH"][j])
                photo.run_photometry(
                    ra_list[i], dec_list[i], data["FILEPATH"][j], save=True
                )
                logging.info("Finished photometry for %s!\n", data["FILEPATH"][j])

        logging.info(
            "Finished updating photometry for %s, generating light curves...", stars[i]
        )
        shutil.copyfile(
            f"{object_dir}/index.csv", f"./Output/indexes/{stars[i]}_index.csv"
        )
        photo.plot_lightcurve(
            f"./{OUTPUT_LOCATION}/{stars[i]}.csv", title=f"{stars[i]} Lightcurve"
        )
