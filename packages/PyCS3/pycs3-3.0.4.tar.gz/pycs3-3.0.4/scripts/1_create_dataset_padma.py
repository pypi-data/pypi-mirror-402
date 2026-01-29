"""
Setup the config file and organise the lens folder.
If you have more than 4 images, you might need to modify the config file and rerun this script.
"""
import argparse as ap
import logging
import os
import sys
from shutil import copyfile
import h5py


import numpy as np

import pycs3.gen.lc_func
import pycs3.gen.mrg
import pycs3.gen.util

loggerformat='%(levelname)s: %(message)s'
logging.basicConfig(format=loggerformat,level=logging.INFO)

def make_lc(filename, band, num_images, err_mean=0.01, err_std=0.005, microlensed=True, regular=True):
    if regular:
        group_path_1 = "regular_3_day_cadence"
        cadence_days = 3
        total_days = 3650
        t = np.arange(0, total_days, cadence_days) + 60949 # time array of shape (1217) # im assuming we start oct 1 2025
        assert t.size == 1217
    else:
        group_path_1 = 'lsst_wfd_cadence'
    if not microlensed:
        group_path_2 = "lensed_mags"
    else:
        group_path_2 = 'microlensed_and_lensed_mags'

    with h5py.File(filename, "r") as f:
        mags = [
            np.array(f[f"{os.path.join(group_path_1, group_path_2)}/image_{i}/{band}"]) for i in range(1, num_images + 1)
        ]
        if group_path_1=='lsst_wfd_cadence':
            t = np.array(f[f"{os.path.join(group_path_1, 'observation_dates')}/{band}"]) + 60949

    # nromal err
    rng = np.random.default_rng(42)
    magerrs = rng.normal(loc=err_mean, scale=err_std, size=(num_images, t.size))
    magerrs = np.clip(magerrs, 1e-4, None)  # ensure non-negative errors
    if num_images==2:
        labels = ['A', 'B']
    else:
        labels = ["A", "B", "C", "D"]

    ### CREATE THE LIGHT CURVE OBJECTS
    # pycs3.gen.lc_func.rdbimport(rdbfile, 'A', 'mag_A', 'magerr_A', "Trial")
    # pycs3.gen.lc_func.factory(jds, mags, magerrs=None, telescopename="Unknown", 
    # object="Unknown", properties=None, verbose=False)

    
    return t, mags, magerrs, labels


def main(lensname, dataname, dataformat, band='i', num_images = 4, microlensed=True, regular = True, work_dir='./'):
    data_directory = os.path.join(work_dir,  "data/")
    pickle_directory = os.path.join(work_dir, "pkl/")
    config_directory = os.path.join(work_dir , "config/")
    simu_directory = os.path.join(work_dir , "Simulation/")
    lens_directory = os.path.join(simu_directory, lensname + "_" + dataname + "/")
    figure_directory = os.path.join(simu_directory, lensname + "_" + dataname, "figure/")
    report_directory = os.path.join(simu_directory, lensname + "_" + dataname, "report/")
    print(figure_directory)

    if not os.path.exists(data_directory):
        print("I will create the data directory for you ! ")
        os.mkdir(data_directory)
    if not os.path.exists(pickle_directory):
        print("I will create the pickle directory for you ! ")
        os.mkdir(pickle_directory)
    if not os.path.exists(simu_directory):
        print("I will create the simulation directory for you ! ")
        os.mkdir(simu_directory)
    if not os.path.exists(config_directory):
        print("I will create the config directory for you ! ")
        os.mkdir(config_directory)
    if not os.path.exists(lens_directory):
        print("I will create the lens directory for you ! ")
        os.mkdir(lens_directory)
    rdbfile = os.path.join(data_directory, lensname + "_" + dataname + f'.{dataformat}')

    if dataformat != 'h5':
        d = np.loadtxt(rdbfile, skiprows=2)
        n_curve = (len(d[0, :]) - 1) / 2
    else:
        n_curve = num_images
    print(os.path.isfile(config_directory + "config_" + lensname + "_" + dataname + ".py"))
    if not os.path.isfile(config_directory + "config_" + lensname + "_" + dataname + ".py"):
        print("I will create the lens config file for you ! ")
        if n_curve == 2 or n_curve == 3 or n_curve == 4:
            if n_curve == 2:
                copyfile("config_default_double.py", config_directory + "config_" + lensname + "_" + dataname + ".py")
            if n_curve == 3:
                copyfile("config_default_triple.py", config_directory + "config_" + lensname + "_" + dataname + ".py")
            elif n_curve == 4:
                copyfile("config_default_quads.py", config_directory + "config_" + lensname + "_" + dataname + ".py")

            cfile = open(os.path.join(config_directory, "config_" + lensname + "_" + dataname + ".py"), 'a')
            cfile.write("#Automaticcaly generated paths : \n")
            cfile.write("work_dir='%s'\n" % work_dir)
            cfile.write("data_directory='%s'\n" % data_directory)
            cfile.write("pickle_directory='%s'\n" % pickle_directory)
            cfile.write("simu_directory='%s'\n" % simu_directory)
            cfile.write("config_directory='%s'\n" % config_directory)
            cfile.write("lens_directory='%s'\n" % lens_directory)
            cfile.write("figure_directory='%s'\n" % figure_directory)
            cfile.write("report_directory='%s'\n" % report_directory)
            cfile.write("data = pickle_directory + '%s_%s.pkl' \n" % (lensname, dataname))
            cfile.close()

            print("Default config file created ! You might want to change the default parameters. ")
            #utils.proquest(True)

        else:
            print(
                " Warning : do you have a quad, a triple or a double ? Make sure you update lcs_label in the config file ! I'll copy the double template for this time !")
            copyfile("config_default_double.py", config_directory + "config_" + lensname + "_" + dataname + ".py")
            cfile = open(os.path.join(config_directory, "config_" + lensname + "_" + dataname + ".py"), 'a')
            cfile.write("#Automaticcaly generated paths : \n")
            cfile.write("work_dir='%s'\n" % work_dir)
            cfile.write("data_directory='%s'\n" % data_directory)
            cfile.write("pickle_directory='%s'\n" % pickle_directory)
            cfile.write("simu_directory='%s'\n" % simu_directory)
            cfile.write("config_directory='%s'\n" % config_directory)
            cfile.write("lens_directory='%s'\n" % lens_directory)
            cfile.write("figure_directory='%s'\n" % figure_directory)
            cfile.write("report_directory='%s'\n" % report_directory)
            cfile.write("data = pickle_directory + '%s_%s.pkl' \n" % (lensname, dataname))
            cfile.close()
            print("Please change the default parameters according to your object and rerun this script.")
            sys.exit()

    if not os.path.exists(figure_directory):
        os.mkdir(figure_directory)
    if not os.path.exists(report_directory):
        os.mkdir(report_directory)

    sys.path.append(config_directory)
    import importlib
    config = importlib.import_module("config_" + lensname + "_" + dataname)

    # import the data

    lcs = []
    
    if dataformat == 'h5':
        print(f"You've entered that file format is h5.")
        print(f'band = {band}')
        if microlensed:
            print("Microlensing present in light curves.")
        else:
            print("No microlensing included in data.")
        if regular:
            print('Using regularly sampled light curves.')
        else:
            print("Using LSST WFD light curves")
        t, mags, magerrs, labels = make_lc(rdbfile, band, n_curve, err_mean=0.01, err_std=0.005, microlensed=microlensed, regular=regular)
        lcs = [
        pycs3.gen.lc_func.factory(t, mag, err,object=name)
            for name, mag, err in zip(labels, mags, magerrs)]
    else:
        for i, a in enumerate(config.lcs_label):
            lcs.append(pycs3.gen.lc_func.rdbimport(rdbfile, a, 'mag_' + a, 'magerr_' + a, dataname))

    if config.display:
        pycs3.gen.mrg.colourise(lcs)
        pycs3.gen.lc_func.display(lcs, showdates=True)

    pycs3.gen.util.writepickle(lcs, pickle_directory + lensname + "_" + dataname + '.pkl')

    if not os.path.exists(lens_directory + 'figure/'):
        os.mkdir(lens_directory + 'figure/')

    print("I have created a new config file for this object ! You probably want to edit it in %s" % (
                config_directory + "config_" + lensname + "_" + dataname + ".py"))


if __name__ == '__main__':
    parser = ap.ArgumentParser(prog="python {}".format(os.path.basename(__file__)),
                               description="Create the data set and organise the file system for a new measurement",
                               formatter_class=ap.RawTextHelpFormatter)
    help_lensname = "name of the lens to process"
    help_dataname = "name of the data set to process (Euler, SMARTS, ... )"
    help_dataformat = "data file type"
    help_work_dir = "name of the working directory"
    parser.add_argument(dest='lensname', type=str,
                        metavar='lens_name', action='store',
                        help=help_lensname)
    parser.add_argument(dest='dataname', type=str,
                        metavar='dataname', action='store',
                        help=help_dataname)
    parser.add_argument(dest='dataformat', type=str,
                        metavar='dataformat', action='store',
                        help=help_dataformat)
    parser.add_argument(dest='band', type=str,
                        metavar='band', action='store',
                        default='i')
    parser.add_argument(dest='num_images', type=int,
                        metavar='num_images', action='store',
                        default=4)
    parser.add_argument('--microlensed', dest='microlensed', action='store_true',
                        help='Set if the data is microlensed (default: True)')
    parser.add_argument('--regular', dest='regular', action='store_true',
                        help='Set if the cadence is regular (default: True)')
    parser.add_argument('--lsst_wfd', dest='lsst_wfd', action='store_true',
                        help='Set if the cadence is lsst_wfd')
    parser.add_argument('--dir', dest='work_dir', type=str,
                        metavar='', action='store', default='./',
                        help=help_work_dir)
    args = parser.parse_args()
    print(args.microlensed,args.lsst_wfd, args.regular)
    main(args.lensname, args.dataname, args.dataformat, args.band, args.num_images, microlensed=args.microlensed, regular=args.regular,work_dir=args.work_dir)

    # lensname, dataname, dataformat, band='i', num_images = 4, microlensed=True, regular = True, work_dir='./'
