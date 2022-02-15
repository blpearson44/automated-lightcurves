#!/usr/bin/env bash
# Simple test script for functionality
python main.py run-photometry 323.4318115915129166 51.123536172913055 "/Users/ben/projects/Senior-Thesis/RX_J2133.7+5107 (V)/RX_J2133.7+5107 V-20201031at040126_-25-1X1-300-V.fts" --save
python main.py plot-lightcurve
