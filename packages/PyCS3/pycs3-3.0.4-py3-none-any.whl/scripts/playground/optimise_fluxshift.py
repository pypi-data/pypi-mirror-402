import argparse as ap
import sys
import os
import importlib
import pycs3.gen.lc_func
import pycs3.gen.stat
import pycs3.gen.util
import pycs3.gen.mrg
import pycs3.spl.multiopt
import numpy as np


def main(lensname, dataname, work_dir='../'):
    os.chdir('..')
    main_path = os.getcwd()
    sys.path.append(work_dir + "config/")
    sys.path.append(work_dir)
    config = importlib.import_module("config_" + lensname + "_" + dataname)

    figure_directory = config.figure_directory + "spline_and_residuals_plots/"
    if not os.path.isdir(figure_directory):
        os.mkdir(figure_directory)

    for i, lc in enumerate(config.lcs_label):
        print("I will aplly a initial shift of : %2.4f days for %s" % (
            config.timeshifts[i], config.lcs_label[i]))

    # Do the optimisation with the splines
    if config.mltype == "splml":
        if config.forcen:
            ml_param = config.nmlspl
            string_ML = "nmlspl"
        else:
            ml_param = config.mlknotsteps
            string_ML = "knml"
    elif config.mltype == "polyml":
        ml_param = config.degree
        string_ML = "deg"
    else:
        raise RuntimeError("I don't know your microlensing type. Choose 'polyml' or 'spml'.")

    for i, kn in enumerate(config.knotstep):
        for j, ml in enumerate(ml_param):
            print(("ML param", j, ml))
            lcs = pycs3.gen.util.readpickle(config.data)
            pycs3.gen.lc_func.applyshifts(lcs, config.timeshifts, [-np.median(lc.getmags()) for lc in
                                                                   lcs])  # remove median and set the time shift to the initial guess
            if ml != 0:
                config.attachml(lcs, ml)  # add microlensing

            spline = config.spl1(lcs, kn=kn)
            pycs3.gen.mrg.colourise(lcs)
            rls = pycs3.gen.stat.subtract(lcs, spline)
            resistat = pycs3.gen.stat.mapresistats(rls)
            print("### BEFORE FLUXSHIFT ###")
            pycs3.gen.lc_func.display(lcs, [spline], showlegend=False, showdelays=True, figsize=(15, 10),
                                      filename='/Users/martin/Desktop/DR2/extra_tests/Nofluxshift_kn%i_nmlspl%i_%s.png' % (
                                      kn,ml, lensname))
            pycs3.gen.stat.plotresiduals([rls],magrad =0.1,
                                         filename='/Users/martin/Desktop/DR2/extra_tests/Nofluxshift_kn%i_nmlspl%i_%s_residuals.png' % (
                                         kn, ml, lensname))

            for x, lc in enumerate(lcs):
                print('Magshift %s: %2.3f' % (lc.object, lc.magshift))
                # lc.applymagshift()
                print('%s : mean %2.4f, std : %2.4f, nruns :%2.4f' % (
                    lc.object, resistat[x]['mean'], resistat[x]['std'], resistat[x]['nruns']))

            print("### AFTER FLUXSHIFT ###")
            pycs3.spl.multiopt.opt_fluxshift(lcs, spline, verbose=True)
            for lc in lcs:
                print('Fluxshift %s: %2.6f' % (lc.object, lc.fluxshift))
                print('Corresponding magshift : ', -2.5 * np.log10(lc.fluxshift))
                lc.applyfluxshift()

            spline = config.spl1(lcs, kn=kn)
            rls = pycs3.gen.stat.subtract(lcs, spline)
            pycs3.gen.lc_func.display(lcs, [spline], showlegend=False, showdelays=True,
                                      figsize=(15, 10),
                                      filename='/Users/martin/Desktop/DR2/extra_tests/fluxshift_kn%i_nmlspl%i_%s.png' % (
                                      kn, ml, lensname))
            pycs3.gen.stat.plotresiduals([rls],magrad =0.1,
                                         filename='/Users/martin/Desktop/DR2/extra_tests/fluxshift_kn%i_nmlspl%i_%s_residuals.png' % (
                                         kn, ml, lensname))
            resistat = pycs3.gen.stat.mapresistats(rls)
            for x,lc in enumerate(lcs) :
                print ('%s : mean %2.4f, std : %2.4f, nruns :%2.4f'%(lc.object, resistat[x]['mean'],resistat[x]['std'],resistat[x]['nruns']))




if __name__ == '__main__':
    parser = ap.ArgumentParser(prog="python {}".format(os.path.basename(__file__)),
                               description="Plot the final results.",
                               formatter_class=ap.RawTextHelpFormatter)
    help_lensname = "name of the lens to process"
    help_dataname = "name of the data set to process (Euler, SMARTS, ... )"
    help_work_dir = "name of the working directory"
    parser.add_argument(dest='lensname', type=str,
                        metavar='lens_name', action='store',
                        help=help_lensname)
    parser.add_argument(dest='dataname', type=str,
                        metavar='dataname', action='store',
                        help=help_dataname)
    parser.add_argument('--dir', dest='work_dir', type=str,
                        metavar='', action='store', default='./',
                        help=help_work_dir)
    args = parser.parse_args()
    main(args.lensname, args.dataname, work_dir=args.work_dir)
