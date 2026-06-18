import networkx as nx
import math
from congress import Congress
import os
import csv

class SmallWorldTools:

    def clustering_coefficient(self, G):
        return nx.average_clustering(G)
        
    def path_length(self, G):
        return nx.average_shortest_path_length(G)

    # FOR APPROXIMATIONS, UNCLEAR WHAT k MEANS
    # Source: https://snap-stanford.github.io/cs224w-notes/preliminaries/measuring-networks-random-graphs
    # APPROXIMATION, WORK IN PROGRESS
    def random_CC(self, k, n):
        return float(k/n)

    # APPROXIMATION, WORK IN PROGRESS
    def random_PL(self, k, n):
        d = float((k - 2)/(k))*(n - 1) + 1
        d = math.log(d)
        d = float(d/(k - 1))
        d += 1
        lm = d - float((k * (k - 1)**d)/((n - 1)*(k - 2)**2))
        lm += float((k*(d*(k - 2) + 1))/((n - 1)*(k - 2)**2))
        return lm

    def small_world(self, G):
        Gcc = sorted(nx.connected_components(G), key=len, reverse=True)
        G = G.subgraph(Gcc[0])
        if nx.is_connected(G):
            n = len(list(G.nodes()))
            # print(n)
            
            # random_G = nx.gnp_random_graph(n, 0.5)
            k = float(2*len(list(G.edges()))/n) # average degree

            CC = self.clustering_coefficient(G)
            PL = self.path_length(G)
            # randCC = self.clustering_coefficient(random_G)
            # randPL = self.path_length(random_G)
            randCC = self.random_CC(k, n)
            randPL = self.random_PL(k, n)
            CC_ratio = float(CC/randCC)
            PL_ratio = float(PL/randPL)

            Q = float(CC_ratio/PL_ratio)
        else:
            print([i for i in nx.connected_components(G)])
        return CC, CC_ratio, PL, PL_ratio, Q



tools = SmallWorldTools()
bill_types = {'house': ['hjres', 'hres', 'hr'], 'senate': ['sjres', 'sres', 's']}

existing_lines = []
l = []
with open("legislative_productivity\DWG_equation.csv", "r", newline='') as f:
    reader = csv.reader(f, delimiter=',')
    for l in reader:
        existing_lines.append(l)
new_data = []
for congress_num in range(93, 118):
    print(congress_num)
    c_data = []
    for b in list(bill_types.keys()):
        datapath = ""
        for root, dirs, files in os.walk(".\\propublica_data\\" + str(congress_num)):
            if root.endswith("bills"):
                datapath = root
                break
        individual_congress = Congress(congress_num, datapath, bill_types)
        individual_congress.build_graph_from_adjlist(b)
        CC, CC_ratio, PL, PL_ratio, Q = tools.small_world(individual_congress.graph)
        c_data += [CC, CC_ratio, PL, PL_ratio, Q]
    new_data.append(c_data)

with open("legislative_productivity\DWG_equation.csv", "w", newline='') as f:
    data = csv.writer(f,delimiter=',')
    for i in range(39):
        existing_line = existing_lines[i]
        new_line = existing_line
        if i >= 14:
            new_line = existing_line + new_data[i - 14]
        data.writerow(new_line)