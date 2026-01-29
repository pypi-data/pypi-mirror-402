import argparse as ap
import os
import pickle
import sys
from multiple_6 import summed_stats, plot_tdc1, create_multiple_silver_sample
import pandas as pd

import matplotlib as mpl
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats


class SimplifiedData:
    """
    Class that will contain the result of the simulation for a specific sample and a specific estimate
    The class has a name, a list of the pair of curves in the sample, the true time delay for each pair of curve, the median and errors for each pair of curves.
    """

    def __init__(self, name, lens, csv_path):
        """
        Create the sample from a name and 5 list

        :type	self: Data
        :param	self: The Data you're creating
        :type	name: str
        :param	name: The name you're giving to your Data
        :type	lens: 1D numpy array
        :param	lens: The list of the indices of the curves in the sample
        :type	csv_path: str
        :param	csv_path: path to the csv files containing the results
        """
        data = pd.read_csv(csv_path)
        keys = data.keys()
        # id = np.intersect1d(data[keys[0]], lens) - 1
        index = np.array([i for i,x in enumerate(data[keys[0]]) if x in lens])

        self.name = name
        self.lens = np.array(lens)
        self._precision = np.array(data[keys[1]])[index]/100.
        self._accuracy = np.array(data[keys[2]])[index]/100.
        self._chi2 = np.array(data[keys[3]])[index]

    def __str__(self):
        """
        Print the attributes from the class
        """
        return ("name :       " + str(self.name) +
                "\nlens :       " + str(self.lens) +
                "\naccuracy :      " + str(self.accuracy) +
                "\nprecision :     " + str(self.precision) +
                "\nchi2 :   " + str(self.chi2))

    def precision(self):
        return self._precision

    def accuracy(self):
        return self._accuracy

    def chi2(self):
        return self._chi2

    def outliers(self):
        """
        return the list of the outliers with chi2 > 10
        """
        return self.lens[self.chi2() > 10]

def filter_FS(sample: np.array, data: SimplifiedData):
    to_reject = sample[data.precision() >= 2.00]
    return np.setdiff1d(sample, to_reject)


def main(name, name_type, number_pair = 1, work_dir = '/Users/martin/Desktop/modules/PyCS3/scripts/', pathdata='./data/results_tdc1_rung3/'):
    # load config file
    sys.path.append(os.path.join(work_dir, "config/multiple"))
    config_multiple_name = __import__("config_multiple_%s" % name)

    Simulation_directory = os.path.join(work_dir, "Simulation")

    Simulation_multiple_directory = os.path.join('./','figure')
    figure_directory = os.path.join(Simulation_multiple_directory, "figure")
    figure_FS_directory = os.path.join(figure_directory, "FS")

    if not os.path.exists(os.path.join(Simulation_directory, "multiple")):
        print("I will create the multiple simulation directory for you ! ")
        os.mkdir(os.path.join(Simulation_directory, "multiple"))
    if not os.path.exists(Simulation_multiple_directory):
        os.mkdir(Simulation_multiple_directory)
    if not os.path.exists(figure_directory):
        os.mkdir(figure_directory)
    if not os.path.exists(figure_FS_directory):
        os.mkdir(figure_FS_directory)
    if (config_multiple_name.display_silver == True):
        figure_SS_directory = figure_directory + "SS/"
        if not os.path.exists(figure_SS_directory):
            os.mkdir(figure_SS_directory)
    if (config_multiple_name.display_gold == True):
        figure_GS_directory = figure_directory + "GS/"
        if not os.path.exists(figure_GS_directory):
            os.mkdir(figure_GS_directory)

    ### Get the true time-delays and update it with the sign from the config file
    truth = []
    data_directory = os.path.join(".", "data")
    truth_directory = os.path.join(data_directory, "truth")
    with open(os.path.join(truth_directory, 'truth_' + name + '.txt'), 'r') as f:
        Lines = f.readlines()
        i = 0
        for line in Lines:
            i += 1
            truth.append(float(line.partition(' ')[2]))
            if (i == number_pair): break
    if (config_multiple_name.sign == -1):
        truth = np.array([-x for x in truth])
    elif (config_multiple_name.sign == 1):
        truth = np.array(truth)
    else:
        print('ERROR : Make sure the sign of the config_multiple file is +1 or -1')
        sys.exit()


    #create the datasets:
    sample = range(1, number_pair + 1)
    FS = np.setdiff1d(sample, config_multiple_name.failed_sim)

    print('####'.center(80, '#'))
    print(" Loading the data for the full sample. ".center(80, '#'))
    print('####'.center(80, '#'))

    baseline = os.path.join(pathdata,'pair_statistics_marg_spline-regdiff.csv')
    regdiff1 = os.path.join(pathdata,'pair_statistics_regdiff_set_1.csv')
    regdiff2 = os.path.join(pathdata,'pair_statistics_regdiff_set_2.csv')
    regdiff3 = os.path.join(pathdata,'pair_statistics_regdiff_set_3.csv')
    regdiff4 = os.path.join(pathdata,'pair_statistics_regdiff_set_4.csv')
    regdiffmarg05 = os.path.join(pathdata,'pair_statistics_regdiff_marg_0.5.csv')
    regdiffmarg0 = os.path.join(pathdata,'pair_statistics_regdiff_marg_0.csv')
    regdiffmarg1000 = os.path.join(pathdata,'pair_statistics_regdiff_marg_1000.csv')
    splinemarg05 = os.path.join(pathdata,'pair_statistics_spline_marg_0.5.csv')
    splinemarg0 = os.path.join(pathdata,'pair_statistics_spline_marg_0.csv')
    splinemarg1000 = os.path.join(pathdata,'pair_statistics_spline_marg_1000.csv')


    both_baseline = SimplifiedData("marg spline-regdiff (baseline)",FS, baseline)
    spl_sigma_0 = SimplifiedData("spline marg ($\\tau_{thresh}$ = 0)",FS, splinemarg0)
    spl_sigma_05 = SimplifiedData("spline marg ($\\tau_{thresh}$ = 0.5)",FS, splinemarg05)
    spl_sigma_1000 = SimplifiedData("spline marg ($\\tau_{thresh}= +\infty$))",FS, splinemarg1000)

    regdiff_set1 = SimplifiedData("regdiff (set 1)", FS, regdiff1)
    regdiff_set2 = SimplifiedData("regdiff (set 2)", FS, regdiff2)
    regdiff_set3 = SimplifiedData("regdiff (set 3)", FS, regdiff3)
    regdiff_set4 = SimplifiedData("regdiff (set 4)", FS, regdiff4)

    regdiff_sigma_0 = SimplifiedData("regdiff marg ($\\tau_{thresh}$ = 0)", FS, regdiffmarg0)
    regdiff_sigma_05 = SimplifiedData("regdiff marg ($\\tau_{thresh}$ = 0.5)", FS, regdiffmarg05)
    regdiff_sigma_1000 = SimplifiedData("regdiff marg ($\\tau_{thresh}= +\infty$))", FS, regdiffmarg1000)

    FS_Datalist = [spl_sigma_0, spl_sigma_05, spl_sigma_1000, regdiff_set1, regdiff_set2,
	             regdiff_set3, regdiff_set4, regdiff_sigma_0, regdiff_sigma_05, regdiff_sigma_1000,
	             both_baseline]

    if (config_multiple_name.display_tdc1 == True):
        plot_tdc1(FS_Datalist, "FS", figure_directory, config_multiple_name.compare_tdc1, number_pair, True)
        if (config_multiple_name.display_filteredFS == True):
            FFSlist = []
            for data in FS_Datalist:
                FFSlist.append(filter_FS(FS,data))

            FFSlist[0], FFSlist[2] = FFSlist[1], FFSlist[1]  # set the same cut for all the marg_spline
            FFSlist[7], FFSlist[9] = FFSlist[8], FFSlist[8]  # set the same cut for all the marg regdiff
            FFSlist[10] = np.intersect1d(FFSlist[1], FFSlist[8])

            print('####'.center(80, '#'))
            print(" Loading the data for the filtered full sample. ".center(80, '#'))
            print('####'.center(80, '#'))

            spl_sigma_0_FFS = SimplifiedData("spline marg ($\\tau_{thresh}$ = 0)", FFSlist[0], splinemarg0)
            spl_sigma_05_FFS = SimplifiedData("spline marg ($\\tau_{thresh}$ = 0.5)", FFSlist[1], splinemarg05)
            spl_sigma_1000_FFS = SimplifiedData("spline marg ($\\tau_{thresh}= +\infty$))", FFSlist[2], splinemarg1000)

            regdiff_set1_FFS = SimplifiedData("regdiff (set 1)", FFSlist[3], regdiff1)
            regdiff_set2_FFS = SimplifiedData("regdiff (set 2)", FFSlist[4], regdiff2)
            regdiff_set3_FFS = SimplifiedData("regdiff (set 3)", FFSlist[5], regdiff3)
            regdiff_set4_FFS = SimplifiedData("regdiff (set 4)", FFSlist[6], regdiff4)

            regdiff_sigma_0_FFS = SimplifiedData("regdiff marg ($\\tau_{thresh}$ = 0)", FFSlist[7], regdiffmarg0)
            regdiff_sigma_05_FFS = SimplifiedData("regdiff marg ($\\tau_{thresh}$ = 0.5)", FFSlist[8], regdiffmarg05)
            regdiff_sigma_1000_FFS = SimplifiedData("regdiff marg ($\\tau_{thresh}= +\infty$))", FFSlist[9], regdiffmarg1000)
            both_baseline_FFS = SimplifiedData("marg spline-regdiff (baseline)", FFSlist[10], baseline)

            FFS_Datalist = [spl_sigma_0_FFS, spl_sigma_05_FFS, spl_sigma_1000_FFS, regdiff_set1_FFS, regdiff_set2_FFS,
                           regdiff_set3_FFS, regdiff_set4_FFS, regdiff_sigma_0_FFS, regdiff_sigma_05_FFS, regdiff_sigma_1000_FFS,
                           both_baseline_FFS]
            plot_tdc1(FFS_Datalist, "FFS", figure_directory, config_multiple_name.compare_tdc1, number_pair, True)

        if (config_multiple_name.display_silver == True):
            SSlist = create_multiple_silver_sample(truth, FS, FS_Datalist)
            for SS in SSlist:
                SS = np.setdiff1d(SS, config_multiple_name.remove_silver_sample)

            print('####'.center(80, '#'))
            print(" Loading the data for the silver sample. ".center(80, '#'))
            print('####'.center(80, '#'))

            spl_sigma_0_SS = SimplifiedData("spline marg ($\\tau_{thresh}$ = 0)", SSlist[0], splinemarg0)
            spl_sigma_05_SS = SimplifiedData("spline marg ($\\tau_{thresh}$ = 0.5)", SSlist[1], splinemarg05)
            spl_sigma_1000_SS = SimplifiedData("spline marg ($\\tau_{thresh}= +\infty$)", SSlist[2], splinemarg1000)

            regdiff_set1_SS = SimplifiedData("regdiff (set 1)", SSlist[3], regdiff1)
            regdiff_set2_SS = SimplifiedData("regdiff (set 2)", SSlist[4], regdiff2)
            regdiff_set3_SS = SimplifiedData("regdiff (set 3)", SSlist[5], regdiff3)
            regdiff_set4_SS = SimplifiedData("regdiff (set 4)", SSlist[6], regdiff4)

            regdiff_sigma_0_SS = SimplifiedData("regdiff marg ($\\tau_{thresh}$ = 0)", SSlist[7], regdiffmarg0)
            regdiff_sigma_05_SS = SimplifiedData("regdiff marg ($\\tau_{thresh}$ = 0.5)", SSlist[8], regdiffmarg05)
            regdiff_sigma_1000_SS = SimplifiedData("regdiff marg ($\\tau_{thresh}= +\infty$)", SSlist[9], regdiffmarg1000)
            both_baseline_SS = SimplifiedData("marg spline-regdiff (baseline)", SSlist[10], baseline)

            SS_Datalist = [spl_sigma_0_SS, spl_sigma_05_SS, spl_sigma_1000_SS, regdiff_set1_SS, regdiff_set2_SS,
                           regdiff_set3_SS, regdiff_set4_SS, regdiff_sigma_0_SS, regdiff_sigma_05_SS, regdiff_sigma_1000_SS,
                           both_baseline_SS]
            plot_tdc1(SS_Datalist, "SS", figure_directory, config_multiple_name.compare_tdc1, number_pair, True)

        if (config_multiple_name.display_gold == True):
            GSlist = []
            for SS in SSlist:
                GSlist.append(np.setdiff1d(SS, config_multiple_name.remove_golden_sample))

            print('####'.center(80, '#'))
            print(" Loading the data for the golden sample. ".center(80, '#'))
            print('####'.center(80, '#'))

            spl_sigma_0_GS = SimplifiedData("spline marg ($\\tau_{thresh}$ = 0)", GSlist[0], splinemarg0)
            spl_sigma_05_GS = SimplifiedData("spline marg ($\\tau_{thresh}$ = 0.5)", GSlist[1], splinemarg05)
            spl_sigma_1000_GS = SimplifiedData("spline marg ($\\tau_{thresh}= +\infty$)", GSlist[2], splinemarg1000)

            regdiff_set1_GS = SimplifiedData("regdiff (set 1)", GSlist[3], regdiff1)
            regdiff_set2_GS = SimplifiedData("regdiff (set 2)", GSlist[4], regdiff2)
            regdiff_set3_GS = SimplifiedData("regdiff (set 3)", GSlist[5], regdiff3)
            regdiff_set4_GS = SimplifiedData("regdiff (set 4)", GSlist[6], regdiff4)

            regdiff_sigma_0_GS = SimplifiedData("regdiff marg ($\\tau_{thresh}$ = 0)", GSlist[7], regdiffmarg0)
            regdiff_sigma_05_GS = SimplifiedData("regdiff marg ($\\tau_{thresh}$ = 0.5)", GSlist[8], regdiffmarg05)
            regdiff_sigma_1000_GS = SimplifiedData("regdiff marg ($\\tau_{thresh} = +\infty$)", GSlist[9], regdiffmarg1000)
            both_baseline_GS = SimplifiedData("marg spline-regdiff (baseline)", GSlist[10], baseline)
            GS_Datalist = [spl_sigma_0_GS, spl_sigma_05_GS, spl_sigma_1000_GS, regdiff_set1_GS, regdiff_set2_GS,
                           regdiff_set3_GS, regdiff_set4_GS, regdiff_sigma_0_GS, regdiff_sigma_05_GS, regdiff_sigma_1000_GS,
                           both_baseline_GS]
            plot_tdc1(GS_Datalist, "GS", figure_directory, config_multiple_name.compare_tdc1, number_pair, True)


        All_datalist = [spl_sigma_05_FFS,spl_sigma_05_SS,spl_sigma_05_GS, regdiff_sigma_05_FFS, regdiff_sigma_05_SS, regdiff_sigma_05_GS]
        prefix = ['FS','SS','GS','FS','SS','GS']
        for i,d in enumerate(All_datalist):
            d.name = prefix[i] + ' ' + d.name

        print('####'.center(80, '#'))
        print(" Plotting Sample together. ".center(80, '#'))
        print('####'.center(80, '#'))
        plot_tdc1(All_datalist, "", figure_directory, config_multiple_name.compare_tdc1, number_pair, True, showregdiffset=True)

        tmp = 'test, f, precision [%], err, accuracy[%],err, chi2,err, X'
        for data in FFS_Datalist:
            stats, error = summed_stats(data, number_pair)
            tmp += "\n" + data.name + "," + str(stats[0]) + "," + str(stats[1] * 100) + "," + str(
                error[0] * 100) + "," + str(stats[2] * 100) + "," + str(error[1] * 100) + "," + str(
                stats[3]) + "," + str(
                error[2]) + "," + str(stats[4])
        with open(os.path.join(Simulation_multiple_directory,'FFS_statistics.csv'), 'w') as f:
            f.write(tmp)
            f.close()



if __name__ == '__main__':
    parser = ap.ArgumentParser(prog="python {}".format(os.path.basename(__file__)),
                               description="Reformat the txt file from the Time Delay Challenge to an usable rdb file.",
                               formatter_class=ap.RawTextHelpFormatter)
    help_name = "name of the sample. Make sure the directory has the same name."
    help_name_type = "Type of the data ie double or quad"
    help_number_pair = "number of pair in the rung folder. Make sure the folder have the format name_pair0"
    help_work_dir = "name of the work directory"
    parser.add_argument(dest='name', type=str,
                        metavar='name', action='store',
                        help=help_name)
    parser.add_argument(dest='name_type', type=str,
                        metavar='name_type', action='store',
                        help=help_name_type)
    parser.add_argument(dest='number_pair', type=int,
                        metavar='number_pair', action='store',
                        help=help_number_pair)
    parser.add_argument('--dir', dest='work_dir', type=str,
                        metavar='', action='store', default='/Users/martin/Desktop/modules/PyCS3/scripts',
                        help=help_work_dir)
    args = parser.parse_args()
    main(args.name, args.name_type, args.number_pair, work_dir=args.work_dir)