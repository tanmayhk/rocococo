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
import networkx_backbone as nb
from polarization_explorations import printable
import numpy as np
import seaborn as sns
from scipy.signal import argrelextrema

tools = SmallWorldTools()
bill_types = {'house': ['hjres', 'hres', 'hr'], 'senate': ['sjres', 'sres', 's']}



def calculate_threshold(data):
    kde = sns.kdeplot(np.array(data))
    line = kde.lines[0]
    x, y = line.get_data()
    dy = np.gradient(y)
    minima = argrelextrema(dy, np.greater)[0]
    x_ind = minima[len(minima) - 1]
    kde.clear()
    return x[x_ind]

def cosponsor_histograms():
    fig = plt.figure()
    nothing_words = ["medal", "commemorat", "renam", "memorial", "condolence", "memory"]
    for congress_num in range(117, 118): #93, 118
            house_cosponsors = []
            senate_cosponsors = []
            print(congress_num, "-")
            datapath = ""
            for root, dirs, files in os.walk(".\\propublica_data\\" + str(congress_num)):
                if root.endswith("bills"):
                    datapath = root
                    break
            individual_congress = Congress(congress_num, datapath, bill_types)
            individual_congress.get_from_json()

            bill_names = individual_congress.all_bills.keys()
            print(len(bill_names))
            for bill in bill_names:
                bill_details = individual_congress.all_bills[bill]
                if 'cosponsors' in bill_details.keys():
                    cosponsors = bill_details['cosponsors']
                    if cosponsors != None:
                        num_cosponsors = 0
                        if type(cosponsors) == type({}):
                            cosponsors = cosponsors['isOriginalCosponsor']
                            num_cosponsors = len(cosponsors) # float(cosponsors.count('True')) # 
                        else:
                            num_cosponsors = len(cosponsors) 
                        if bill[0] == 'h':
                            house_cosponsors.append(num_cosponsors)
                        else:
                            senate_cosponsors.append(num_cosponsors)
            print(len(house_cosponsors) + len(senate_cosponsors))

            # print(sorted(house_cosponsors))
            # print("")
            # print(sorted(senate_cosponsors))

            # M1 = 0
            # M2 = 0
            # M1 = calculate_threshold(house_cosponsors) # max(house_cosponsors) - 20 #
            # M2 = calculate_threshold(senate_cosponsors) # max(senate_cosponsors) - 20 # 
            # print(M1, M2)

            # nothings = {"h": [0, 0], "s": [0, 0]}  
            # cosponsor = {"h": [], "s": []}          
            
            for bill in bill_names:
                bill_details = individual_congress.all_bills[bill]
                if 'cosponsors' in bill_details.keys():
                    cosponsors = bill_details['cosponsors']
                    if cosponsors != None:
                        num_cosponsors = individual_congress.cosponsor_metric(cosponsors)

                        is_nothing = False
                        bill_text = individual_congress.get_bill_text(bill_details)
                        for w in nothing_words:
                            if w in bill_text:
                                is_nothing = True

                        if is_nothing:
                            print(bill, num_cosponsors, bill_text)
                            print("")

            # print(cosponsor)
            
            # plt.hist(house_cosponsors, bins=len(set(house_cosponsors)))
            # plt.suptitle("House " + str(congress_num) + " bill ORIGINAL cosponsor histogram")
            # plt.savefig("descriptive_statistic_plots\\cosponsor_histograms\\all_cosponsors\\HOUSE_WACK_ORIGINAL_PROPORTION" + str(congress_num) + ".jpg")
            # plt.clf()

            # plt.hist(senate_cosponsors, bins=len(set(senate_cosponsors)))
            # plt.suptitle("Senate " + str(congress_num) + " bill ORIGINAL cosponsor histogram")
            # plt.savefig("descriptive_statistic_plots\\cosponsor_histograms\\all_cosponsors\\SENATE_WACK_ORIGINAL_PROPORTION" + str(congress_num) + ".jpg")
            # plt.clf()

def backbone_analysis():
    house = []
    senate = []
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
                # individual_congress.build_graph_from_adjlist(b)
                # individual_congress.get_from_json()
                # individual_congress.build_bipartite_from_adjlist(b)
                individual_congress.build_backbone_from_adjlist(b)

                B = individual_congress.backbone
                # G = individual_congress.graph
                characteristic = tools.density(B)
                if b == 'house':
                    house.append(characteristic)
                else:
                    senate.append(characteristic)
    for i in house:
        print(printable(i))
    print("")
    for j in senate:
        print(printable(j))

def verify_filtered_graphs():
    house = []
    senate = []
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
            individual_congress.build_filtered_from_adjlist(b)

            G1 = individual_congress.graph
            G2 = individual_congress.filtered
            n = len(list(G1.edges())) - len(list(G2.edges()))
            if b[0] == 'h':
                house.append(n)
            else:
                senate.append(n)

            # print(G1.edges.data())
            # for e in G2.edges.data():
            #     bills = e[2]['bills'].split(" ")
            #     for b in bills:
            #         bill_dict = individual_congress.all_bills[b]
            #         t = individual_congress.get_bill_text(bill_dict)
            #         for w in individual_congress.nothing_words:
            #             if w in t:
            #                 print(b, t)
    for i in house:
        print(i)
    print("")
    for i in senate:
        print(i)



# cosponsor_histograms()
# backbone_analysis()

# verify_filtered_graphs()