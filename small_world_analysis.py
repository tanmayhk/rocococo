import networkx as nx
import math
from congress import Congress
import os
import csv

class SmallWorldTools:

    def density(self, G):
        return nx.density(G)

    def edge_cut(self, G):
        parties = nx.get_node_attributes(G, "party")
        if parties == {}:
            return -1
        else:
            # print(G.edges.data())
            D_nodes = [i for i in parties.keys() if parties[i] == 'D']
            # D_subgraph = G.subgraph(D_nodes)
            R_nodes = [i for i in parties.keys() if parties[i] == 'R']
            # R_subgraph = G.subgraph(R_nodes)
            c = nx.cut_size(G, D_nodes, R_nodes)
            m = G.size(weight="weight")
            return float(c/m)
    
    def modularity(self, G): # CURRENTLY SET TO UNWEIGHTED-----------------------
        parties = nx.get_node_attributes(G, "party")
        # print(parties)
        if parties == {}:
            return -1
        else:
            # print(G.edges.data())
            D_nodes = [i for i in parties.keys() if parties[i] == 'D']
            # I_nodes = [i for i in parties.keys() if parties[i] == 'I']
            # D_subgraph = G.subgraph(D_nodes)
            R_nodes = [i for i in parties.keys() if parties[i] == 'R']

            G = G.subgraph(D_nodes + R_nodes)
            # print("num_nodes:", len(D_nodes), len(R_nodes), len(D_nodes + R_nodes))
            
            m = nx.community.modularity(G, [set(D_nodes), set(R_nodes)]) # , weight=None #, set(I_nodes) 

            return m

    def minority_modularity(self, G): # CURRENTLY SET TO UNWEIGHTED-----------------------
        parties = nx.get_node_attributes(G, "ethnicity")
        # print(parties)
        if parties == {}:
            return -1
        else:
            # print(G.edges.data())
            D_nodes = [i for i in parties.keys() if parties[i] == 'White']
            # I_nodes = [i for i in parties.keys() if parties[i] == 'I']
            # D_subgraph = G.subgraph(D_nodes)
            R_nodes = [i for i in parties.keys() if parties[i] != 'White']
    
            G = G.subgraph(D_nodes + R_nodes)
            # print("num_nodes:", len(D_nodes), len(R_nodes), len(D_nodes + R_nodes))
            
            m = nx.community.modularity(G, [set(D_nodes), set(R_nodes)]) # , weight=None #, set(I_nodes) 
    
            return m
        
    def max_modularity(self, G):
        parties = nx.get_node_attributes(G, "party")
        # print(parties)
        if parties == {}:
            return -1
        else:
            # print(G.edges.data())
            D_nodes = [i for i in parties.keys() if parties[i] == 'D']
            # I_nodes = [i for i in parties.keys() if parties[i] == 'I']
            # D_subgraph = G.subgraph(D_nodes)
            R_nodes = [i for i in parties.keys() if parties[i] == 'R']

            G = G.subgraph(D_nodes + R_nodes)
            # print("num_nodes:", len(D_nodes), len(R_nodes), len(D_nodes + R_nodes))
        
            c = nx.community.greedy_modularity_communities(G, weight='weight')
            m = nx.community.modularity(G, c)
            return m

    def largest_clique_size(self, G):
        clique = nx.make_max_clique_graph(G)
        return len(list(clique.nodes()))

    def triangle_metrics(self, G):
        t = list(nx.triangles(G).values())
        return [sum(t)//3, float(sum(t)/len(t)), float((float(sum(t)/len(t)))/(sum(t)//3))]
    
    def connectivity_metrics(self, G):
        return [nx.node_connectivity(G), nx.average_node_connectivity(G)]

    def clustering_coefficient(self, G):
        return nx.average_clustering(G)
        
    def path_length(self, G):
        return nx.average_shortest_path_length(G)

    def individual_clustering_coefficient(self, G, v):
        return nx.clustering(G, v, weight='weight')

    def individual_inter_intra_partisanship(self, G, v):
        parties = nx.get_node_attributes(G, "party")
        party = parties[v]
        intra = 0
        inter = 0
        for e in G.edges(v, data=True):
            v2 = e[1]
            if parties[v2] != party:
                inter += e[2]['weight'] # 1 #
            else:
                intra += e[2]['weight'] # 1 #
        return float(intra/(inter + intra))


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
        if Gcc != []:
            G = G.subgraph(Gcc[0])
            if nx.is_connected(G):
                n = len(list(G.nodes()))
                # print(n)
                
                # random_G = nx.gnp_random_graph(n, 0.5)

                CC = self.clustering_coefficient(G)
                PL = self.path_length(G)
                # randCC = self.clustering_coefficient(random_G)
                # randPL = self.path_length(random_G)
                k = float(2*len(list(G.edges()))/n) # average degree
                Q = -1
                if k != 0 and float((k - 2)/(k))*(n - 1) + 1 > 0 and n != 1 and k != 2:
                    randCC = self.random_CC(k, n)
                    randPL = self.random_PL(k, n)
                    CC_ratio = float(CC/randCC)
                    PL_ratio = float(PL/randPL)

                    Q = float(CC_ratio/PL_ratio)
            else:
                print([i for i in nx.connected_components(G)])
            return [CC, PL, Q] # [CC, PL, CC_ratio, PL_ratio, Q] # [CC_ratio, PL_ratio] #
        else:
            return [-1, -1, -1]



# tools = SmallWorldTools()
# bill_types = {'house': ['hjres', 'hres', 'hr'], 'senate': ['sjres', 'sres', 's']}

# existing_lines = []
# l = []
# with open("legislative_productivity\DWG_equation.csv", "r", newline='') as f:
#     reader = csv.reader(f, delimiter=',')
#     for l in reader:
#         existing_lines.append(l)

# new_data = []
# for congress_num in range(93, 118):
#     print(congress_num)
#     c_data = []
#     for b in list(bill_types.keys()):
#         datapath = ""
#         for root, dirs, files in os.walk(".\\propublica_data\\" + str(congress_num)):
#             if root.endswith("bills"):
#                 datapath = root
#                 break
#         individual_congress = Congress(congress_num, datapath, bill_types)
#         individual_congress.build_graph_from_adjlist(b)
#         CC, CC_ratio, PL, PL_ratio, Q = tools.small_world(individual_congress.graph)
#         c_data += [CC, CC_ratio, PL, PL_ratio, Q]
#     new_data.append(c_data)

# with open("legislative_productivity\DWG_equation.csv", "w", newline='') as f:
#     data = csv.writer(f,delimiter=',')
#     for i in range(39):
#         existing_line = existing_lines[i]
#         new_line = existing_line
#         if i >= 14:
#             new_line = existing_line + new_data[i - 14]
#         data.writerow(new_line)