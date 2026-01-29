import pycs3.gen.lc_func
import numpy as np
import pycs3.gen.mrg
import pycs3.spl.multiopt
import pycs3.spl.topopt
import argparse as ap
import os


def main(lensname, dataname, work_dir='../'):
    rdbfile = '/Users/martin/Desktop/modules/PyCS3/scripts/data/%s_%s.rdb'%(lensname,dataname)

    lcs = [pycs3.gen.lc_func.rdbimport(rdbfile, object='A', magcolname='mag_A', magerrcolname='magerr_A'),
           pycs3.gen.lc_func.rdbimport(rdbfile, object='B', magcolname='mag_B', magerrcolname='magerr_B'),
           pycs3.gen.lc_func.rdbimport(rdbfile, object='C', magcolname='mag_C', magerrcolname='magerr_C'),
           pycs3.gen.lc_func.rdbimport(rdbfile, object='D', magcolname='mag_D', magerrcolname='magerr_D')]

    pycs3.gen.mrg.colourise(lcs)
    td = [0, 7.5, -6.7,-14.1] #td for WG0214
    # td = [0, -30.5, 8.6,-71.9] #td for 2M1134
    # ZP = 31.61395808280451 #for 0214
    knotstep = 35
    # knotstep = 15

    pycs3.gen.lc_func.applyshifts(lcs, td, [-np.median(lc.getmags()) for lc in
                                                               lcs])  # remove median and set the time shift to the initial gues
    if 1 :
        # pycs3.spl.multiopt.opt_magshift(lcs)
        # for lc in lcs :
        #     print('Magshift %s: '%lc.object, lc.magshift)
        #     lc.applymagshift()

        pycs3.gen.lc_func.display(lcs, [], showlegend=False, showdelays=True, figsize=(15, 10),
                                  filename='screen')
        pycs3.gen.lc_func.display(lcs, [], showlegend=False, showdelays=True, figsize=(15, 10),
                                  filename='/Users/martin/Desktop/DR2/extra_tests/applyshift/%s_%s_before.png'%(lensname,dataname))

    spline = pycs3.spl.topopt.opt_fine([lcs[0]], spline=None, nit=10, shifttime=False, crit="r2",
                 knotstep=knotstep, stabext=300.0, stabgap=20.0, stabstep=4.0, stabmagerr=-2.0,
                 bokeps=knotstep/3., boktests=10, bokwindow=None,
                 distribflux=False, splflat=True, verbose=True)

    pycs3.gen.lc_func.display([lcs[0]], [spline], showlegend=True, showdelays=True, figsize=(15, 10),
                              filename='screen')


    pycs3.spl.multiopt.opt_fluxshift(lcs, spline, verbose=True)

    for lc in lcs:
        print('Fluxshift %s: %2.6f' % (lc.object, lc.fluxshift))
        print('Magshift %s: %2.6f' % (lc.object, lc.magshift))
        # mean_flux = np.mean(10**(-(lc.mags+lc.magshift-ZP) /2.5))
        # print("Mean flux :  %2.6f "%(mean_flux))
        # print('Fluxshift percentage : %2.6f'%(lc.fluxshift/ mean_flux *100))
        print('Corresponding magshift : ', -2.5 * np.log10(lc.fluxshift))

    pycs3.gen.lc_func.display(lcs, [], showlegend=False, showdelays=True, figsize=(15, 10),
                              filename='screen')

    for lc in lcs :
        lc.timeshift = 0.0
        lc.applyfluxshift()

    rdbout = '/Users/martin/Desktop/DR2/extra_tests/applyshift/%s_%stdfs.rdb'%(lensname, dataname)
    pycs3.gen.util.multilcsexport(lcs, rdbout)


    lcs2 = [pycs3.gen.lc_func.rdbimport(rdbout, object='A', magcolname='mag_A', magerrcolname='magerr_A'),
           pycs3.gen.lc_func.rdbimport(rdbout, object='B', magcolname='mag_B', magerrcolname='magerr_B'),
           pycs3.gen.lc_func.rdbimport(rdbout, object='C', magcolname='mag_C', magerrcolname='magerr_C'),
           pycs3.gen.lc_func.rdbimport(rdbout, object='D', magcolname='mag_D', magerrcolname='magerr_D')]

    pycs3.gen.mrg.colourise(lcs2)
    pycs3.gen.lc_func.applyshifts(lcs2, td, [0,0,0,0])  # remove median and set the time shift to the initial guess
    pycs3.gen.lc_func.display(lcs2, [], showlegend=False, showdelays=True, figsize=(15, 10),
                              filename='screen')
    pycs3.gen.lc_func.display(lcs2, [], showlegend=False, showdelays=True, figsize=(15, 10),
                              filename='/Users/martin/Desktop/DR2/extra_tests/applyshift/%s_%s_after.png'%(lensname,dataname))


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