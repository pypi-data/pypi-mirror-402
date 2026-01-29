import pycs3.gen.lc_func
import pycs3.spl.topopt
import pycs3.gen.mrg
import pycs3.gen.splml
import pycs3.regdiff.multiopt
import pycs3.regdiff.rslc
import numpy as np

myknotstep = 25  # [15,20,25,30]
mlknotstep = 200  # [150,180,200,250,300]

# shift_in_time = [0.,0.,-10.,-60.]
shift_in_time = [1.0, 0.0, 0.3, -94]
# shift_in_time = [-1.0,0.0,-0.3,-117]

rdbfile = "/Users/martin/Desktop/modules/PyCS3/scripts/data/fake1131_ECAM.rdb"

lcs = [
    pycs3.gen.lc_func.rdbimport(rdbfile, 'A', 'mag_A', 'magerr_A', "Trial"),
    pycs3.gen.lc_func.rdbimport(rdbfile, 'B', 'mag_B', 'magerr_B', "Trial"),
    pycs3.gen.lc_func.rdbimport(rdbfile, 'C', 'mag_C', 'magerr_C', "Trial"),
    pycs3.gen.lc_func.rdbimport(rdbfile, 'D', 'mag_D', 'magerr_D', "Trial")
]
pycs3.gen.mrg.colourise(lcs)  # Gives each curve a different colour.
magsft = [-np.median(lc.getmags()) for lc in lcs]
pycs3.gen.lc_func.applyshifts(lcs, shift_in_time, magsft)  # remove median and set the time shift to the initial guess


def spl(lcs, knotstep):
    # spline = pycs3.spl.topopt.opt_rough(lcs, nit=5, knotstep=30, verbose=False)
    # spline = pycs3.spl.topopt.opt_fine(lcs, nit=10, knotstep=knotstep, verbose=False)
    spline = pycs3.spl.topopt.opt_fine(lcs, knotstep=knotstep, bokeps=knotstep/3., nit=5, stabext=100)
    return spline


# pycs3.gen.lc_func.applyshifts(lcs, shift_in_time, shift_in_mag)  # we had an initial guess of the time delay
for lc in lcs:
    pycs3.gen.splml.addtolc(lc, knotstep=mlknotstep)  # we attach microlensing to the LightCurve object

spline = spl(lcs, myknotstep)
pycs3.gen.lc_func.display(lcs, [spline], figsize=(12, 9), showdelays=True, showlegend=False,
                          title=r"$\mathrm{Free-knot\ Splines }$")
# print ("Time delays:")
# print (pycs3.gen.lc_func.getnicetimedelays(lcs, separator="\n", to_be_sorted=True))
### Output the time delays
index = 1  # This is the index of image B
n = len(lcs)
worklcs = pycs3.gen.lc_func.objsort(lcs, ret=True, verbose=False)
couples = [(worklcs[index], worklcs[i]) for i in range(n) if i != index]
# print( '\n'.join( ["%s%s = %+7.2f" % (lc1.object, lc2.object, lc2.timeshift - lc1.timeshift) for (lc1, lc2) in couples] ) )
tds = ["%+7.2f" % (lc2.timeshift - lc1.timeshift) for (lc1, lc2) in couples]

file_object = open('time_delays.dat', 'a')
file_object.write(','.join(tds) + '\n')
file_object.close()
