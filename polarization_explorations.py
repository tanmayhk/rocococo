import networkx as nx
import math
from congress import Congress
import os
import scipy
import pandas as pd
from small_world_analysis import SmallWorldTools
import matplotlib.pyplot as plt

from csvtex import create_latex_table, save_latex_table

tools = SmallWorldTools()
bill_types = {'house': ['hjres', 'hres', 'hr'], 'senate': ['sjres', 'sres', 's']}

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

    for congress_num in range(93, 118): #93-118
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
            # parties = nx.get_node_attributes(G, "party")
            
            # D_nodes = [i for i in parties.keys() if parties[i] == 'D']
            # D_subgraph = G.subgraph(D_nodes)

            # R_nodes = [i for i in parties.keys() if parties[i] == 'R']
            # R_subgraph = G.subgraph(R_nodes)

            characteristic = tools.modularity(G)
            if b == 'house':
                house_characteristic.append(characteristic)
            if b == 'senate':
                senate_characteristic.append(characteristic)

    label = ["MODULARITY"]
    print(printable(["HOUSE_" + i for i in label]))
    for i in house_characteristic:
        print(printable(i))

    print("")
    print(printable(["SENATE_" + i for i in label]))
    for i in senate_characteristic:
        print(printable(i))

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


# gen_data()

generate_plots()

# send_to_latex("correlations", "Pearson $r$ correlations between Democrat/Republican and all-Congress metrics", "legislative_productivity\stat_correlations.csv", "legislative_productivity\stat_correlations.tex")