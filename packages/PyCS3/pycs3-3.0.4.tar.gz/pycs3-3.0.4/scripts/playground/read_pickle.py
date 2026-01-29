import pycs
import numpy as np

lensname = '2M1134'
dataname = 'WFI'
pklfile = '/Users/martin/Desktop/MCMC_pycs/Simulation/2M1134_WFI/figure/initopt_WFI_ks12_nmlspl2.pkl'

lcs, spline = pycs.gen.util.readpickle(pklfile)
pycs.gen.lc.display(lcs, [spline], showlegend=True, showdelays=True, filename="screen")


rdbout = '/Users/martin/Desktop/DR2/extra_tests/applyshift/%s_%s_splinemodel.rdb'%(lensname, dataname)

jds = np.linspace(58110,58330, 500)
spline_mag = spline.eval(jds)

spline_lc = pycs.gen.lc.lightcurve(object='spline')
spline_lc.mags = spline_mag
spline_lc.jds = jds
spline_lc.mask = np.ones(len(spline_mag))
spline_lc.properties = np.ones(len(spline_mag))
spline_lc.labels = np.ones(len(spline_mag))
spline_lc.magerrs = np.ones(len(spline_mag)) * 0.000001

pycs.gen.util.multilcsexport([spline_lc], rdbout)

pycs.gen.lc.display([spline_lc], [], showlegend=True, showdelays=True, filename="screen")