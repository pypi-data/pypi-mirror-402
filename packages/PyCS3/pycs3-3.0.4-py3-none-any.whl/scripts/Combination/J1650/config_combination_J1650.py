#####################
#  Configuration file for combining data set
#####################
full_lensname ='SDSSJ1650+4251'
delay_labels = ["AB"]
lcs_label = ["A","B"]
testmode = True #Set to False for more precision
display = False

combi_name = 'REG_Mercator+Maidanak_extraMercator+Maidanak_Mercator+Maidanak+USNO'  #give a name to your combination
data_sets = ['Mercator','Maidanak']  #select the data sets
# marg_to_combine =['marginalisation_final' for sets in data_sets] #give the name of the marginalisation to combine
# marg_to_combine =['marginalisation_spline', 'marginalisation_spline_no25'] #give the name of the marginalisation to combine
marg_to_combine =['marginalisation_regdiff', 'marginalisation_regdiff'] #give the name of the marginalisation to combine
sigma_to_combine=[0.5 for sets in data_sets]  #give the corresponding sigma used for the marginalisation
sigma_thresh = 0.0 #sigme threshold for the PyCS-sum estimate, leave it to 0 for a true marginalisation

#Additionnal spline marginalisation to plots (only if show_spline = True):
marg_to_combine_spline =['marginalisation_spline', 'marginalisation_spline_no25'] #give the name of the marginalisation to combine
sigma_to_combine_spline=[0.5 for sets in data_sets]

#Additionnal regdiff marginalisation to plots (only if show_spline = True):
# marg_to_combine_regdiff =['marginalisation_regdiff' for sets in data_sets] #give the name of the marginalisation to combine
marg_to_combine_regdiff =[] #give the name of the marginalisation to combine
# sigma_to_combine_regdiff=[0.5 for sets in data_sets]
sigma_to_combine_regdiff=[]

#Additionnal data set to show on the plot but not included in the combination : 
extra_data_sets = ['Maidanak+Mercator']
# extra_data_sets = []
# extra_marg_to_combine =['marginalisation_final' for sets in extra_data_sets] #give the name of the extra marginalisation to combine
# extra_marg_to_combine =['marginalisation_spline' for sets in extra_data_sets] #give the name of the extra marginalisation to combine
extra_marg_to_combine =['marginalisation_regdiff' for sets in extra_data_sets] #give the name of the extra marginalisation to combine
# extra_marg_to_combine_regdiff =['marginalisation_regdiff' for sets in extra_data_sets] #give the name of extra sploine marginalisation to combine
extra_marg_to_combine_regdiff =[] #give the name of extra sploine marginalisation to combine
extra_marg_to_combine_spline =[] #give the name of the extra regdiff marginalisation to combine
# extra_marg_to_combine_spline =['marginalisation_spline' for sets in extra_data_sets] #give the name of the extra regdiff marginalisation to combine
extra_sigma_to_combine=[0.5 for sets in extra_data_sets]  #give the corresponding sigma used for the  final marginalisation

# extra_sigma_to_combine_regdiff=[0.5 for sets in extra_data_sets]  #give the corresponding sigma used for the regdiff marginalisation
extra_sigma_to_combine_regdiff=[]  #give the corresponding sigma used for the regdiff marginalisation
# extra_sigma_to_combine_spline=[0.5 for sets in extra_data_sets]  #give the corresponding sigma used for the spline marginalisation
extra_sigma_to_combine_spline=[]  #give the corresponding sigma used for the spline marginalisation
