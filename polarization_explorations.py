import networkx as nx
import math
from congress import Congress
import os
import scipy
from statsmodels.api import add_constant, OLS
from statsmodels.stats import descriptivestats
import pandas as pd
from small_world_analysis import SmallWorldTools
import matplotlib.pyplot as plt
import csv
import io
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
    house_characteristic = [[], []]
    senate_characteristic = [[], []]
    # ET = pd.read_csv("github_legislator_data\\msu_ippsr_house_data_93-117.csv")
    for congress_num in range(93, 118): #93, 118
        print(congress_num, "-")
        for b in list(bill_types.keys()):
            print(b)
            datapath = ""
            for root, dirs, files in os.walk(".\\propublica_data\\" + str(congress_num)):
                if root.endswith("bills"):
                    datapath = root
                    break
            
            individual_congress = Congress(congress_num, datapath, bill_types)
            individual_congress.build_graph_from_adjlist(b)
            individual_congress.get_from_json()
            # individual_congress.filter_nothing_bills(b, True)
            individual_congress.build_filtered_from_adjlist(b)
        
            G = individual_congress.graph
            F = individual_congress.filtered
            if b == 'house':
                house_characteristic[0].append(len(list(F.edges)))
                house_characteristic[1].append(len(list(G.edges)))
            else:
                senate_characteristic[0].append(len(list(F.edges)))
                senate_characteristic[1].append(len(list(G.edges)))


            # # individual_congress.add_parties_from_github(b) # Comment out if not done yet
            # # individual_congress.verify_congresspeople(b, G.nodes.data())
            # # if b == 'house':
            # #     individual_congress.add_house_predicted_ethnicities(b, ET)

            # parties = nx.get_node_attributes(F, "party")
            # minorities = nx.get_node_attributes(F, "ethnicity")
            # all_keys = [i for i in minorities.keys() if i in parties.keys()]
            # print([len([i for i in all_keys if parties[i] == 'D']), len([i for i in all_keys if parties[i] == 'R']), len([i for i in all_keys if minorities[i] == "White" and parties[i] == 'D']), len([i for i in all_keys if minorities[i] == "White" and parties[i] == 'R'])])

            # for j in range(2):
            #     party = ['D', 'R'][j]
            #     # MINORITIES
            #     minority_nodes = [i for i in all_keys if minorities[i] == "White" and parties[i] == party]
            #     minority_subgraph =  F.subgraph(minority_nodes)
            #     characteristic = tools.small_world(minority_subgraph)
            #     characteristic2 = tools.density(minority_subgraph)
            #     characteristic.append(characteristic2)                    

            #     house_characteristic[j].append(characteristic)

            #  b == 'house':
            #   parties = nx.get_node_attributes(G, "party")
            #   minorities = nx.get_node_attributes(G, "ethnicity")
            #   all_keys = [i for i in minorities.keys() if i in parties.keys()]

            #   house_characteristic.append([len([i for i in all_keys if parties[i] == 'D']), len([i for i in all_keys if parties[i] == 'R']), len([i for i in all_keys if minorities[i] != "White" and parties[i] == 'D']), len([i for i in all_keys if minorities[i] != "White" and parties[i] == 'R'])])
            #   # minority_nodes = [i for i in all_keys if minorities[i] != "White" and parties[i] == 'R']
            #   # minority_subgraph =  G.subgraph(minority_nodes)
            #   # small_world = tools.small_world(minority_subgraph)
            #   # characteristic = tools.density(minority_subgraph)
            #   # small_world.append(characteristic)

            #   # house_characteristic.append(small_world)
    
    print("")
    # label = ["MODULARITY"]
    # print(printable(["HOUSE_" + i for i in label]))
    for j in range(2):
        print(["FILTERED", "UNFILTERED"][j])

        for i in house_characteristic[j]:
            print(printable(i))

        print("")
        # print(printable(["SENATE_" + i for i in label]))
        for i in senate_characteristic[j]:
            print(printable(i))
        print("")
        print("==================================")
        print("")

def gen_degree_histograms(chamber):
    savepath = "descriptive_statistic_plots\\" + chamber + "_DEGREE\\"
    if not os.path.exists(savepath):
        os.makedirs(savepath)
    
    for congress_num in range(93, 118): #93, 118
        datapath = ""
        for root, dirs, files in os.walk(".\\propublica_data\\" + str(congress_num)):
            if root.endswith("bills"):
                datapath = root
                break
        individual_congress = Congress(congress_num, datapath, bill_types)
        individual_congress.build_graph_from_adjlist(chamber)
        
        G = individual_congress.graph
        print(len(list(G.nodes())))

        # parties = nx.get_node_attributes(G, "party")
        
        # D_nodes = [i for i in parties.keys() if parties[i] == 'D']
        # D_subgraph = G.subgraph(D_nodes)

        # R_nodes = [i for i in parties.keys() if parties[i] == 'R']
        # R_subgraph = G.subgraph(R_nodes)

        # all_degrees = [val for (node, val) in G.degree()] # nx.clustering(G).values()
        # D_degrees =  [val for (node, val) in D_subgraph.degree()] #nx.clustering(D_subgraph).values()
        # R_degrees =  [val for (node, val) in R_subgraph.degree()] #nx.clustering(R_subgraph).values()

        # all_CC_stats = descriptivestats.describe(all_degrees)
        # D_stats = descriptivestats.describe(D_degrees)
        # R_stats = descriptivestats.describe(R_degrees)

        # d = scipy.stats.kstest(D_degrees, all_degrees)
        # r = scipy.stats.kstest(R_degrees, all_degrees)
        # print(d.statistic, r.statistic, d.statistic < r.statistic, "|", d.pvalue < 0.05, r.pvalue < 0.05)

        # plt.hist(D_degrees, label='Democrat', alpha=0.3333, color='blue')
        # plt.hist(R_degrees, label='Republican', alpha=0.3333, color='red')
        # plt.hist(all_degrees, label='All Congress', alpha=0.3333, color='black')
        # plt.savefig(savepath + str(congress_num) + ".jpg")
        # plt.clf()


def generate_minority_plots():
    metrics = ["CC", "PL", "Q", "DENSITY"]
    minority_data = pd.read_csv("legislative_productivity\\filtered_minority_metrics.csv")
    chamber = "HOUSE"
    years = list(minority_data["YEARS"])
    for metric in metrics:
        label = chamber + "_" + metric
        allc_data = list(minority_data[label])
        dem_data = list(minority_data["DEM_" + label])
        rep_data = list(minority_data["REP_" + label])
        # f = plt.figure()
        # f.set_figwidth(24)
        # f.set_figheight(8)
        # plt.plot(years, dem_data, label='Democrat', color='blue')
        # plt.plot(years, rep_data, label='Republican', color='red')
        # plt.plot(years, allc_data, label='All Congress', color='black')
        for ethnicity in [("WHITE_", "White", "--"), ("MIN_", "Minority", ":")]:
            
            dem_ethnic_data = [None if (i == -1 or i == 0) else i for i in list(minority_data["DEM_" + ethnicity[0] + label])]
            rep_ethnic_data = [None if (i == -1 or i == 0) else i for i in list(minority_data["REP_" + ethnicity[0] + label])]
   
            # plt.plot(years, dem_ethnic_data, label='Democrat (' + ethnicity[1] + ')', color='blue', linestyle=ethnicity[2])
            # plt.plot(years, rep_ethnic_data, label='Republican (' + ethnicity[1] + ')', color='red', linestyle=ethnicity[2])

            # if ethnicity[1] == "Minority":

            #     dem_r = scipy.stats.pearsonr(dem_ethnic_data, allc_data)
            #     rep_r = scipy.stats.pearsonr(rep_data, allc_data)
            #     dem_stat = dem_r.statistic
            #     rep_stat = rep_r.statistic
            #     print(label, dem_stat, dem_r.pvalue < 0.05, rep_stat, rep_r.pvalue < 0.05, "Comparison:", dem_stat - rep_stat)
            #     # print("")

            # "DEM_" : ["Democratic", 'blue', "-"], "REP_" : ["Republican", 'red', "-"], "DEM_MIN_": ['Democrat (Minority)', 'blue', ':'], "DEM_WHITE_": ['Democrat (White)', 'blue', '--'], "REP_MIN_":['Republican (Minority)', 'red', ':'], "REP_WHITE_": ['Republican (White)', 'red', '--']
            groups_119 = [{"DEM_MIN_": ['Democrat (Minority)', 'blue', ':'], "DEM_WHITE_": ['Democrat (White)', 'blue', '--'], "REP_MIN_":['Republican (Minority)', 'red', ':'], "REP_WHITE_": ['Republican (White)', 'red', '--']}]
            for j in range(1):
                f = plt.figure()
                f.set_figwidth(24)
                f.set_figheight(8)
                if ethnicity[1] == "Minority":
                    
                    X = minority_data[[i + label for i in list(groups_119[j].keys())]]
                    y = minority_data["HOUSE_MAX_MODULARITY"]# ["DEM_", "REP_"][j] + label
                    X = add_constant(X)
                    est = OLS(y, X.astype(float)).fit()
                    print(est.summary())
                    f.suptitle("R^2 = " + str(est.rsquared), fontsize=20)
                    for i in range(len(list(groups_119[j].keys()))):
                        k = list(groups_119[j].keys())[i]
                        v = groups_119[j][k]
                        group_coeff = est.params[k + label]
                        power_over_time = [group_coeff/i for i in list(minority_data[k])]
                        plt.plot(years, power_over_time, label=v[0] + ": " + str(group_coeff), color=v[1], linestyle=v[2])
                plt.legend()
                plt.savefig("descriptive_statistic_plots\\filtered_graph\\regression_coefficient_graphs\\MAX_MODULARITY\\" + metric + "_MODULARITY_ETHNICITIES_ADJCOEFF" + ".jpg")
                plt.clf()
        # plt.legend()
        # plt.savefig("descriptive_statistic_plots\\house_minority\\" + label + ".jpg")
        # plt.clf()
        
def generate_plots():
    metrics = ["EDGES_FILTERED_PROPORTION_OF_ORIGINAL"] # ["CC", "CC_RATIO", "PL", "PL_RATIO", "Q", "DENSITY"]
    dem = pd.read_csv("legislative_productivity\\filtered_democrat_descriptive_stats.csv")
    rep = pd.read_csv("legislative_productivity\\filtered_republican_descriptive_stats.csv")
    allc = pd.read_csv("legislative_productivity\\filtered_statistics.csv")

    years = list(dem["YEARS"])
    # print(years)
    f = plt.figure()
    f.set_figwidth(24)
    f.set_figheight(8)
    for chamberd in [("HOUSE", "House Edges Removed (Proportion)", "-"), ("SENATE", "Senate Edges Removed (Proportion)", "--")]:
        chamber = chamberd[0]
        for metric in metrics:
            label = chamber + "_" + metric
            # dem_data = list(dem[label])
            # rep_data = list(rep[label])
            allc_data = list(allc[label])
            plt.plot(years, allc_data, label=chamberd[1], color='black', linestyle=chamberd[2])
            # plt.plot(years, dem_data, label='Democrat', color='blue')
            # plt.plot(years, rep_data, label='Republican', color='red')

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
            # print(label, round(dem_stat, 3), dem_r.pvalue < 0.05, round(rep_stat, 3), rep_r.pvalue < 0.05, "Comparison:", round(dem_stat - rep_stat, 3))
            # # print("")
    v = "EDGES_REMOVED_PROPORTION"
    plt.legend()
    plt.savefig("descriptive_statistic_plots\\filtered_graph\\filtering_plots\\" + v + ".jpg")
    plt.clf()

data_filepath = ".\\legislative_productivity\\"
OLS_filepath = ".\\OLS_tables_small_world\\"

def OLS_regressions(title, y1, y2, independent_variables, dependent_variable, to_save):
    ind1 = ((y1 - 1947)//2)
    ind2 = ((y2 - 1947)//2)
    data_table = pd.read_csv(data_filepath + "DWG_equation.csv") 

    X = data_table[independent_variables][ind1:ind2]
    y = data_table[dependent_variable][ind1:ind2]
    X = add_constant(X)
    est = OLS(y, X.astype(float)).fit()
    
    S = est.summary()
    if to_save:
        csv_text = S.as_csv()
        # Use StringIO to treat string as a file
        data_io = io.StringIO(csv_text)
        # Read the string data
        reader = csv.reader(data_io)
        # Write to a CSV file
        with open(OLS_filepath + title + ".csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for row in reader:
                writer.writerow(row)
    else:
        print(S)

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

# gen_degree_histograms("house")

# gen_data()
# generate_plots()
# generate_minority_plots()

["N of LAWS", "UNI/DIV", "1st 1/2 term", "MOOD", "Budgetary", "Rep. Pres.", "Tea", "HOUSE_CC", "HOUSE_PL", "HOUSE_CC_RATIO", "HOUSE_PL_RATIO", "HOUSE_Q", "SENATE_CC", "SENATE_PL", "SENATE_CC_RATIO", "SENATE_PL_RATIO", "SENATE_Q"]
ind_vars = ["UNI/DIV", "1st 1/2 term", "Rep. Pres."]
y1 = 1973
y2 = 2021
is_print = False
OLS_regressions("house_modularity_NO_minorities,UNFILTERED", y1, y2, ind_vars, "HOUSE_UNWEIGHTED_MODULARITY", is_print)
OLS_regressions("house_modularity_minorities,UNFILTERED", y1, y2, ind_vars + ["House Minorities"], "HOUSE_UNWEIGHTED_MODULARITY", is_print)
print("\n\n================================================================\n\n")
OLS_regressions("senate_modularity_NO_minorities,UNFILTERED", y1, y2, ind_vars, "SENATE_UNWEIGHTED_MODULARITY", is_print)
OLS_regressions("senate_modularity_minorities,UNFILTERED", y1, y2, ind_vars + ["Senate Minorities"], "SENATE_UNWEIGHTED_MODULARITY", is_print)
                             
# send_to_latex("tea", "Pear", "legislative_productivity\stat_correlations.csv", "legislative_productivity\stat_correlations.tex")