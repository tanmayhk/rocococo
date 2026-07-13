import networkx as nx
import math
from congress import Congress
import os
import scipy
from statsmodels.api import add_constant, OLS
import pandas as pd
from small_world_analysis import SmallWorldTools
import matplotlib.pyplot as plt


from csvtex import create_latex_table, save_latex_table

tools = SmallWorldTools()
bill_types = {'house': ['hjres', 'hres', 'hr'], 'senate': ['sjres', 'sres', 's']}

def format_digits(float_num):
    return str(round(float_num, 3))

def send_to_latex(mylabel, title, csv_filepath, save_title):
    table = create_latex_table(csv_filepath, caption=title, label='tab:'+mylabel)
    save_latex_table(table, save_title)

def printable(metric):
    if type(metric) == type([]):
        return str(metric)[1:len(str(metric))-1]
    else:
        return metric

def gen_data():
    house_characteristic = []
    senate_characteristic = []

    for congress_num in range(99, 118): #93-118
        print(congress_num, "-")
        c_data = []
        for b in list(bill_types.keys()):
            print(b)
            datapath = ""
            for root, dirs, files in os.walk(".\\propublica_data\\" + str(congress_num)):
                if root.endswith("bills"):
                    datapath = root
                    break
            individual_congress = Congress(congress_num, datapath, bill_types)
            individual_congress.build_graph_from_adjlist(b)
            
            # individual_congress.add_parties_from_github(b) # Comment out if not done yet

            G = individual_congress.graph
            
            individual_congress.verify_congresspeople(b, G.nodes.data())

    #         # parties = nx.get_node_attributes(G, "party")
            
    #         # D_nodes = [i for i in parties.keys() if parties[i] == 'D']
    #         # D_subgraph = G.subgraph(D_nodes)

    #         # R_nodes = [i for i in parties.keys() if parties[i] == 'R']
    #         # R_subgraph = G.subgraph(R_nodes)

    #         characteristic = tools.modularity(G)
    #         if b == 'house':
    #             house_characteristic.append(characteristic)
    #         if b == 'senate':
    #             senate_characteristic.append(characteristic)

    # label = ["MODULARITY"]
    # print(printable(["HOUSE_" + i for i in label]))
    # for i in house_characteristic:
    #     print(printable(i))

    # print("")
    # print(printable(["SENATE_" + i for i in label]))
    # for i in senate_characteristic:
    #     print(printable(i))

def generate_plots():
    metrics = ["MODULARITY"]
    dem = pd.read_csv("legislative_productivity\\democrat_descriptive_stats.csv")
    rep = pd.read_csv("legislative_productivity\\republican_descriptive_stats.csv")
    allc = pd.read_csv("legislative_productivity\\all_congress_descriptive_stats.csv")

    years = list(dem["YEARS"])
    # print(years)
    for chamber in ["HOUSE", "SENATE"]:
        for metric in metrics:
            label = chamber + "_" + metric
            dem_data = list(dem[label])
            rep_data = list(rep[label])
            allc_data = list(allc[label])

            f = plt.figure()
            f.set_figwidth(24)
            f.set_figheight(8)
            plt.plot(years, dem_data, label='Democrat', color='blue')
            plt.plot(years, rep_data, label='Republican', color='red')
            plt.plot(years, allc_data, label='All Congress', color='black')
            plt.savefig("descriptive_statistic_plots\\" + label + ".jpg")
            plt.clf()

            # dem_error_sum = 0
            # rep_error_sum = 0
            # num_errors = 0
            # for i in range(len(dem_data)):
            #     dem_error_sum += (allc_data[i] - dem_data[i])**2
            #     rep_error_sum += (allc_data[i] - rep_data[i])**2
            #     num_errors += 1
            # dem_error = float(dem_error_sum/num_errors)
            # rep_error = float(rep_error_sum/num_errors)
            # # print(label, dem_error, rep_error, dem_error > rep_error)

            # dem_r = scipy.stats.pearsonr(dem_data, allc_data)
            # rep_r = scipy.stats.pearsonr(rep_data, allc_data)
            # dem_stat = dem_r.statistic
            # rep_stat = rep_r.statistic
            # print(label, dem_stat, dem_r.pvalue < 0.05, rep_stat, rep_r.pvalue < 0.05, "Comparison:", dem_stat - rep_stat)
            # # print("")

data_filepath = ".\\legislative_productivity\\"
OLS_filepath = ".\\OLS_tables_small_world\\"

def OLS_regressions(y1, y2, independent_variables, dependent_variable):
    ind1 = ((y1 - 1947)//2)
    ind2 = ((y2 - 1947)//2)
    data_table = pd.read_csv(data_filepath + "DWG_equation.csv") 

    X = data_table[independent_variables][ind1:ind2]
    y = data_table[dependent_variable][ind1:ind2]
    X = add_constant(X)
    est = OLS(y, X.astype(float)).fit()
    
    print(est.summary())

    # coeffs = list(est.params)
    # errors = list(est.bse)
    # pvals = list(est.pvalues)
    # print(str(y1) + "-" + str(y2) + " &")
    # for i in range(len(independent_variables) + 1):
    #     if pvals[i] < 0.05:
    #         print("$" + format_digits(coeffs[i]) + "^*$\t&")
    #     else:
    #         print(format_digits(coeffs[i]))
    #     print("(" + format_digits(errors[i]) + ")\t&")
    # print(str(ind2 - ind1 + 1) + "\t&")
    # print(format_digits(est.rsquared) + "\t&")
    # print(format_digits(est.rsquared_adj) + "\t\t&")

gen_data()

# generate_plots()

# ["N of LAWS", "UNI/DIV", "1st 1/2 term", "MOOD", "Budgetary", "Rep. Pres.", "Tea", "HOUSE_CC", "HOUSE_PL", "HOUSE_CC_RATIO", "HOUSE_PL_RATIO", "HOUSE_Q", "SENATE_CC", "SENATE_PL", "SENATE_CC_RATIO", "SENATE_PL_RATIO", "SENATE_Q"]
# OLS_regressions(1973, 2021, ["N of LAWS", "UNI/DIV", "1st 1/2 term", "Rep. Pres.", "Tea"], "HOUSE_MODULARITY")
                             
# send_to_latex("tea", "Pear", "legislative_productivity\stat_correlations.csv", "legislative_productivity\stat_correlations.tex")