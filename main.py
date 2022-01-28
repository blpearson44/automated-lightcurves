import photometryplus.photometry as pho

star_RA = 323.4318115915129166
star_DEC = 51.123536172913055
# input_file = "/Users/ben/projects/Senior-Thesis/test.fts"
input_file = "/Users/ben/projects/Senior-Thesis/RX_J2133.7+5107 (V)/RX_J2133.7+5107 V-20200505at082302_-25-1X1-300-V.fts"
dark = "/Users/ben/projects/Senior-Thesis/calibrations/darks/master_dark_20211007_1X1_300.fits"
flats = "/Users/ben/projects/Senior-Thesis/calibrations/flats/master_flat_20210722_1X1_V.fits"

pho.changeSettings(useBiasFlag=0)

out = pho.runPhotometry(
    star_RA,
    star_DEC,
    input_file,
    dark,
    "",
    flats,
)
print(out)


pho.printReferenceToFile(out.referenceStars)
