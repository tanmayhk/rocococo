import os
import xmltodict
import json
import networkx as nx
import networkx_backbone as nb
import plotly.graph_objects as go
import time
import csv
from pypdf import PdfReader
import datetime
import re
import pandas as pd
import numpy as np
import math

# Data source: https://projects.propublica.org/datastore/#congressional-data-bulk-legislation-bills

class Congress:
    def __init__(self, number, filepath, bill_types):
        self.number = number
        
        self.savepath = "parsed\\" + str(self.number) + "_parsed\\"
        if not os.path.exists(self.savepath):
            os.makedirs(self.savepath)
        
        self.savepath += str(self.number)
        self.filepath = filepath # filepath to bills folder in extracted ProPublica ZIP file
        self.bill_types = bill_types # os.listdir(filepath)
        self.bill_names = []
        self.is_xml = False

        self.all_bills = {}
        self.legislators = {}

        self.graph = nx.Graph()
        self.bipartite = nx.Graph()
        self.backbone = nx.Graph()
        self.filtered = nx.Graph()

        self.nothing_words = ["medal", "commemorat", "renam", "memorial", "condolence", "memory"]
    
    def clean_XML_string(self, xml_text):
        to_remove = ["item"]
        for tag in to_remove:
            xml_text = xml_text.replace("<" + tag + ">", "")
            xml_text = xml_text.replace("</" + tag + ">", "")
        return xml_text

    def get_legislators(self, leg_list):
        if type(leg_list) == type([]) and type(leg_list[0]) == type({}):
            keys = list(leg_list[0].keys())
            leg_list = {k : [i[k] for i in leg_list] for k in keys}


        existing_legislators = list(self.legislators.keys())
        other_keys = list(leg_list.keys())

        id_key = ""
        fields_to_remove = []
        if 'bioguideId' in other_keys:
            id_key = 'bioguideId'
            fields_to_remove = ['bioguideId', 'identifiers', 'sponsorshipDate', 'isByRequest', "isOriginalCosponsor", "sponsorshipWithdrawnDate"]
        elif 'bioguide_id' in other_keys:
            id_key = 'bioguide_id'
            fields_to_remove = ['bioguide_id', "sponsored_at", "withdrawn_at"]
        elif 'thomas_id' in other_keys:
            id_key = 'thomas_id'
            fields_to_remove = ['thomas_id', "sponsored_at", "withdrawn_at"]

        bioguides = leg_list[id_key]
        for k in other_keys:
            if leg_list[k] == None or (type(leg_list[k]) == type([]) and None in leg_list[k]):
                fields_to_remove.append(k)

        for k in fields_to_remove:
            if k in other_keys:
                other_keys.remove(k)

        if type(bioguides) == type([]): # multiple legislators
            for b in range(len(bioguides)):
                if bioguides[b] not in existing_legislators:
                    details = {key: leg_list[key][b] for key in other_keys if len(leg_list[key]) == len(bioguides)}
                    # print(details)
                    self.legislators[bioguides[b]] = details
                    if bioguides[b] not in list(self.graph.nodes()):
                        self.graph.add_nodes_from([(bioguides[b], details)])

        elif type(bioguides) == type(""):
            if bioguides not in existing_legislators:
                details = {key: leg_list[key] for key in other_keys}
                # print(details)
                self.legislators[bioguides] = details
                if bioguides not in list(self.graph.nodes()):
                    self.graph.add_nodes_from([(bioguides, details)])
        return bioguides

    def compare_minority_white_legislators(self):
        found_legs = 0
        total_legs = 0
        similarity_dict = {}
        vertex_list = self.filtered.nodes.data()
        for v1 in vertex_list:
            name = v1[0]
            data = v1[1]
            if data['is_white'] == False:
                total_legs += 1
                leg = self.find_most_similar_white_legislator(name)
                if leg != None:
                    found_legs += 1
                    similarity_dict[name] = leg[0]
        print("Similarity statistics:", found_legs, total_legs, found_legs/total_legs)
        return similarity_dict


    def find_most_similar_white_legislator(self, minority):
        vertex_list = self.filtered.nodes.data()
        similarities = []
        for v1 in vertex_list:
            name = v1[0]
            data = v1[1]
            if data['is_white'] == True:
                similarity = self.get_cosine_similarity(minority, name)
                if similarity != None:
                    similarities.append((name, data, similarity))
        if similarities == [] or similarities == None:
            return None
        leg = max(similarities, key = lambda i: i[2])
        return leg


    def get_cosine_similarity(self, v0, v1):
        v0_data = self.filtered.nodes[v0]
        v1_data = self.filtered.nodes[v1]
        v0_length = 0
        v1_length = 0
        v0_v1_dot = 0

        vector_elements = ['votepct', 'dwnom1', 'dwnom2', 'seniority']
        factor = {'votepct': 0.01, 'dwnom1': 1, 'dwnom2': 1, 'seniority': 0.02}
        for k in vector_elements:
            if k not in v0_data.keys() or k not in v1_data.keys():
                return None

        for k in vector_elements:
            v0_k = v0_data[k]*factor[k]
            v1_k = v1_data[k]*factor[k]
            v0_v1_dot += v0_k*v1_k
            v0_length += (v0_k)**2
            v1_length += (v1_k)**2
        v0_length = math.sqrt(v0_length)
        v1_length = math.sqrt(v1_length)

        return float((v0_v1_dot)/(v0_length*v1_length))
            

    def get_bills(self, dump=False, save_graph=False):
        t0 = time.time()
        for bill_category in list(self.bill_types.keys()):
            bill_formats = self.bill_types[bill_category]
            edges = []
            weighted_edges = []
            self.graph = nx.Graph()
            for bill_type in bill_formats:
                print(bill_type)
                specific_dir = self.filepath + "\\" + bill_type
                for (dirpath, dirnames, filenames) in os.walk(specific_dir):
                    if dirnames == []:
                        bill_name = dirpath.split("\\")
                        bill_name = bill_name[len(bill_name) - 1]

                        bill_dictionary = {}
                        sponsor_field = ""
                        cosponsor_field = ""

                        if "fdsys_billstatus.xml" in filenames:
                            bill_XML = dirpath + "\\fdsys_billstatus.xml" 
                            with open(bill_XML, "r", encoding = 'cp850') as f:
                                xml_text = "".join(f.readlines())
                                xml_text = self.clean_XML_string(xml_text)
                                bill_dictionary = xmltodict.parse(xml_text)['billStatus']['bill']
                                self.bill_names.append(bill_name)
                                sponsor_field = "sponsors"
                                cosponsor_field = "cosponsors"
                                self.is_xml = True
                        elif "data.json" in filenames:
                            bill_json = dirpath + "\\" + "data.json"
                            with open(bill_json, "r", encoding="utf-8") as f:
                                bill_dictionary = json.load(f)
                                sponsor_field = "sponsor"
                                cosponsor_field = "cosponsors"
                                self.is_xml = False

                        self.all_bills[bill_name] = bill_dictionary
                        
                        fields = list(bill_dictionary.keys())
                        if sponsor_field in fields and bill_dictionary[sponsor_field] not in [None, []]:
                            sponsor = self.get_legislators(bill_dictionary[sponsor_field])
                            if type(sponsor) == type([]):
                                sponsor = sponsor[0]
                            if cosponsor_field in fields and bill_dictionary[cosponsor_field] not in [None, []]:
                                cosponsor = self.get_legislators(bill_dictionary[cosponsor_field])
                                if type(cosponsor) != type([]):
                                    cosponsor = [cosponsor]
                                for c in cosponsor:
                                    edge = [sponsor, c]
                                    # print(sponsor, c)
                                    if edge not in edges:
                                        edges.append(edge)
                                        weighted_edges.append([edge[0], edge[1], {"weight": 1}])
                                    else:
                                        ind = edges.index(edge)
                                        weighted_edges[ind][2]["weight"] += 1
            self.graph.add_edges_from(weighted_edges)    
            if save_graph:
                nx.write_graphml_lxml(self.graph, self.savepath + str(bill_category) + ".graphml")

        if dump:
                # json_str = json.dumps(self.all_bills)
                with open(self.savepath + "_bills.json", "w", encoding='utf-8') as f:
                    json.dump(self.all_bills, f, ensure_ascii=False)
                # json_str = json.dumps(self.legislators)
                with open(self.savepath + "_legislators.json", "w", encoding='utf-8') as f:
                    json.dump(self.legislators, f, ensure_ascii=False)

        self.graph = nx.Graph()
        t1 = time.time()
        print("Bills retrieved:", t1 - t0, "s")
        return self.is_xml
    
    def get_from_json(self):
        with open(self.savepath + "_bills.json", "r", encoding='utf-8') as f:
            self.all_bills = json.load(f)
        with open(self.savepath + "_legislators.json", "r", encoding='utf-8') as f:
            self.legislators = json.load(f)
    
    def get_important_bill_info(self, bill_dictionary):
        text = []
        existing_fields = list(bill_dictionary.keys())
        important_fields = ["type", "number", "congress", "introducedDate"]
        for f in important_fields:
            if f in existing_fields:
                text.append(bill_dictionary[f])
        text = " ".join(text)
        imp_dict = {"details": text}
        return imp_dict

    def shorten_party(self, party_str):
        if "Republican" in party_str:
            return "R"
        elif "Democrat" in party_str:
            return "D"
        else:
            return "I"

    def add_parties_from_github(self, bill_type):
        G = self.graph
        congresspeople = G.nodes()
        # print(congresspeople)
        party_dict = {}
        if nx.get_node_attributes(G, "party") == {}:
            for c in congresspeople:
                skip = False
                with open('github_legislator_data\\legislators-historical.csv', encoding="utf-8", newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if c == row['thomas_id'] or c == row['bioguide_id']:
                            party_dict[c] = self.shorten_party(row['party'])
                            skip = True
                            break
                if skip:
                    with open('github_legislator_data\\legislators-current.csv', encoding="utf-8", newline='') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            if c == row['thomas_id'] or c == row['bioguide_id']:
                                party_dict[c] = self.shorten_party(row['party'])
                                skip = True
                                break
        nx.set_node_attributes(self.graph, party_dict, "party")
        nx.write_graphml_lxml(self.graph, self.savepath + str(bill_type) + ".graphml")

    def build_graph_from_adjlist(self, bill_type):
        self.graph = nx.read_graphml(self.savepath + str(bill_type) + ".graphml")
    
    def build_bipartite_from_adjlist(self, bill_type):
        self.bipartite = nx.read_graphml(self.savepath + str(bill_type) + "_bipartite.graphml")

    def build_backbone_from_adjlist(self, bill_type):
        self.backbone = nx.read_graphml(self.savepath + str(bill_type) + "_backbone.graphml")
    
    def build_filtered_from_adjlist(self, bill_type):
        self.filtered = nx.read_graphml(self.savepath + str(bill_type) + "_filtered.graphml")
    
    def verify_congresspeople(self, bill_type, people_names):
        name_dict = {}
        state_dict = {}
        title_dict = {}
        party_dict = {}
        icpsr_dict = {}

        t0 = time.time()
        with open("github_legislator_data\\legislators-historical.json", 'r', encoding='utf-8') as f:
            old_legislators = json.load(f)
            with open("github_legislator_data\\legislators-current.json", 'r', encoding='utf-8') as f2:
                new_legislators = json.load(f2)
                legislators = old_legislators + new_legislators

                date_format1 = "%B %d, %Y"
                date_format2 = "%Y-%m-%d"
                start_of_congress = datetime.datetime.strptime("January 3, " + str(1787 + 2*self.number), date_format1)
                end_of_congress = datetime.datetime.strptime("January 3, " + str(1789 + 2*self.number), date_format1)

                for person in people_names:
                    person_id = person[0]
                    # print(person_id in thomas, person_id in bioguides, person_id not in thomas and person_id not in bioguides)
                    person_details = person[1]
                    to_print = True
                    reason = "person not found"
                    for l in legislators:
                        if ('bioguide' in l['id'].keys() and person_id == l['id']['bioguide']) or ('thomas' in l['id'].keys() and person_id == l['id']['thomas']):
                            reason = "no term in range"
                            if 'icpsr' in l['id'].keys():
                                icpsr_dict[person_id] = l['id']['icpsr']
                    #         for term in l['terms']:
                    #             start = datetime.datetime.strptime(term['start'], date_format2)
                    #             end = datetime.datetime.strptime(term['end'], date_format2)
                    #             if (start <= start_of_congress and end >= start_of_congress) or (start >= start_of_congress and start <= end_of_congress):
                    #                 if 'name' not in person_details.keys() and 'fullName' not in person_details.keys():
                    #                     full_name = l['name']['last'] + ", " + l['name']['first']
                    #                     if 'middle' in l['name'].keys():
                    #                         full_name += l['name']['middle'][0] + "."
                    #                     if 'suffix' in l['name'].keys():
                    #                         full_name += l['name']['suffix'][0] + "."
                    #                     name_dict[person_id] = full_name
                    #                 if 'party' not in person_details.keys():
                    #                     party_dict[person_id] = term['party'][0]
                    #                 if 'state' not in person_details.keys():
                    #                     state_dict[person_id] = term['state']
                    #                 if 'title' not in person_details.keys():
                    #                     title_dict[person_id] = term['type'].capitalize()
                    #                 to_print = False
                    #                 break
                    # if to_print:
                    #     print(person_details, reason)
                        
        t1 = time.time()
        print("Congressional verification:", t1 - t0, "s")
        # nx.set_node_attributes(self.graph, name_dict, "name")
        # nx.set_node_attributes(self.graph, state_dict, "state")
        # nx.set_node_attributes(self.graph, title_dict, "title")
        # nx.set_node_attributes(self.graph, party_dict, "party")
        nx.set_node_attributes(self.graph, icpsr_dict, "icpsr")

        nx.write_graphml_lxml(self.graph, self.savepath + str(bill_type) + ".graphml")

    def add_house_district_info(self, bill_type, details_table):
        t0 = time.time()

        vertex_list = self.filtered.nodes.data()
        votepct_dict = {}
        dwnom1_dict = {}
        dwnom2_dict = {}
        seniority_dict = {}
        gender_dict = {}
        age_dict = {}

        format = '%Y-%m-%d'
        y1 = 2*self.number + 1787
        y2 = y1 + 2
        congress_start = datetime.datetime.strptime(str(y1) + '-01-03', format)
        congress_end = datetime.datetime.strptime(str(y2) + '-01-03', format)

        for v in vertex_list:
            person_details = v[1]
            for i in range(len(details_table)):
                if details_table['bioguide'][i] == v[0] or ('icpsr' in person_details.keys() and details_table['icpsr'][i] == person_details['icpsr']):
                    gender = details_table['gender_foster'][i]
                    if gender == gender:
                        gender_dict[v[0]] = gender
                    dwnom1 = details_table['dwnom1'][i]
                    if dwnom1 == dwnom1:
                        dwnom1_dict[v[0]] = dwnom1
                    dwnom2 = details_table['dwnom2'][i]
                    if dwnom2 == dwnom2:
                        dwnom2_dict[v[0]] = dwnom2

                    term_start = datetime.datetime.strptime(details_table['start'][i], format)
                    term_end = datetime.datetime.strptime(details_table['end'][i], format)
                    if (term_end <= congress_end and term_end >= congress_start) or (term_end > congress_end and term_start <= congress_end):
                        seniority = details_table['seniority'][i]
                        if seniority == seniority:
                            seniority_dict[v[0]] = seniority
                        age = details_table['age'][i]
                        if age == age:
                            age_dict[v[0]] = age
                        votepct = details_table['votepct'][i]
                        if votepct == votepct:
                            votepct_dict[v[0]] = votepct

        # print(votepct_dict)
        # print("======")
        # print(seniority_dict)
        # print("=====")
        # print(gender_dict)
        
        nx.set_node_attributes(self.filtered, votepct_dict, "votepct")
        nx.set_node_attributes(self.filtered, dwnom1_dict, "dwnom1")
        nx.set_node_attributes(self.filtered, dwnom2_dict, "dwnom2")
        nx.set_node_attributes(self.filtered, seniority_dict, "seniority")
        nx.set_node_attributes(self.filtered, gender_dict, "gender")
        nx.set_node_attributes(self.filtered, age_dict, "age")

        nx.write_graphml_lxml(self.filtered, self.savepath + str(bill_type) + "_filtered.graphml")

        t1 = time.time()
        print("House district info:", t1 - t0, "s")

    def add_house_parties_manually(self, bill_type):
        party_dict = {}
        vertex_list = self.filtered.nodes.data()
        for v in vertex_list:
            person_details = v[1]
            if 'name' in person_details.keys():
                full_name = person_details['name']
            else:
                full_name = person_details['fullName'][5:].split(" [")[0]
            if 'party' not in person_details.keys():
                found = False
                with open("temp_parties.txt", mode="r") as f:
                    new_parties = f.readlines()
                    for n in new_parties:
                        q = n.replace("\n", "")
                        if str(v[0]) in q:
                            q = q.split(",")
                            party = q[1]
                            party_dict[v[0]] = p
                            found = True
                if not found:
                    p = input(full_name + ' party: ')
                    party_dict[v[0]] = p
                    with open("temp_ethnicities.txt", mode="a") as f:
                        f.write(str(v[0]) + "," + p + "\n")

        nx.set_node_attributes(self.graph, party_dict, "party")
        nx.set_node_attributes(self.filtered, party_dict, "party")
        nx.write_graphml_lxml(self.graph, self.savepath + str(bill_type) + ".graphml")
        nx.write_graphml_lxml(self.filtered, self.savepath + str(bill_type) + "_filtered.graphml")
        

    def add_house_predicted_ethnicities(self, bill_type, ethnicity_table):
        t0 = time.time()
        vertex_list = self.graph.nodes.data()

        is_white_dict = {}
        ethnicity_dict = {}
        to_input_manually = []
        
        c = 0
        for v in vertex_list:
            person_details = v[1]
            if 'name' in person_details.keys():
                full_name = person_details['name']
            else:
                full_name = person_details['fullName'][5:].split(" [")[0]
            # print(full_name)
            ethnicity_found = False
            is_no_info = True
            for i in range(len(ethnicity_table)):
                if ethnicity_table['bioguide'][i] == v[0] or ('icpsr' in person_details.keys() and ethnicity_table['icpsr'][i] == person_details['icpsr']):
                    # print(full_name, "found")
                    ind_to_put = i
                    black = ethnicity_table['afam'][i]
                    latino = ethnicity_table['latino'][i]
                    asian = ethnicity_table['asian'][i]
                    ethnicity = ""
                    non_white = ethnicity_table['non_white'][i]

                    # print(full_name, black, latino, asian, non_white)
                    if black == black or latino == latino or asian == asian or non_white == non_white:
                        is_no_info = False

                    if black == np.float64(1.0):
                        ethnicity = "African American"
                        ethnicity_found = True
                    if latino == np.float64(1.0):
                        ethnicity = "Latino"
                        ethnicity_found = True
                    if asian == np.float64(1.0):
                        ethnicity = "Asian"
                        ethnicity_found = True

                    if ethnicity_found:
                        ethnicity_dict[v[0]] = ethnicity
                        is_white_dict[v[0]] = False
                        # print(ethnicity)
                        break

                    if non_white == np.float64(0.0):
                        ethnicity_dict[v[0]] = "White"
                        is_white_dict[v[0]] = True
                        ethnicity_found = True
                        # print("White")
                        break
                    elif non_white == np.float64(1.0):
                        is_white_dict[v[0]] = False
                        ethnicity_found = True
                        break

            if not is_no_info and not ethnicity_found:
                ethnicity_dict[v[0]] = "White"
                is_white_dict[v[0]] = True
                ethnicity_found = True
                # print("White")

            if not ethnicity_found:
                with open("temp_ethnicities.txt", mode="r") as f:
                    new_ethnicities = f.readlines()
                    for n in new_ethnicities:
                        q = n.replace("\n", "")
                        if str(v[0]) in q:
                            q = q.split(",")
                            ethnicity = q[1]
                            ethnicity_dict[v[0]] = ethnicity
                            is_white_dict[v[0]] = (ethnicity == 'White')
                            ethnicity_found = True
                            # print(ethnicity)

            if not ethnicity_found:
                # print("No details in congress", self.number, ":", full_name, v[0])
                to_input_manually.append((v[0], full_name))

            c += 1
        t1 = time.time()
        
        for v in to_input_manually:
            ethnicity = input(v[1] + " ethnicity = ")
            ethnicity_dict[v[0]] = ethnicity
            is_white_dict[v[0]] = (ethnicity == 'White')
            with open("temp_ethnicities.txt", mode="a") as f:
                f.write(str(v[0]) + "," + ethnicity + "\n")
        

        nx.set_node_attributes(self.graph, is_white_dict, "is_white")
        nx.set_node_attributes(self.graph, ethnicity_dict, "ethnicity")     
        nx.set_node_attributes(self.filtered, is_white_dict, "is_white")
        nx.set_node_attributes(self.filtered, ethnicity_dict, "ethnicity")    

        nx.write_graphml_lxml(self.graph, self.savepath + str(bill_type) + ".graphml")
        nx.write_graphml_lxml(self.filtered, self.savepath + str(bill_type) + "_filtered.graphml")
        print("House ethnicities:", t1 - t0, "s")


    def update_bill_edges(self, chamber, save_graph):
        attrs = {}

        sponsor_field = "sponsors"
        cosponsor_field = "cosponsors"
        for b in self.all_bills.keys():
            if b[0] == chamber[0]:
                self.bipartite.add_node(b)
                bill_dictionary = self.all_bills[b]
                fields = list(bill_dictionary.keys())
                if "sponsor" in fields:
                    sponsor_field = "sponsor"
                if sponsor_field in fields and bill_dictionary[sponsor_field] not in [None, []]:
                    sponsor = self.get_legislators(bill_dictionary[sponsor_field])
                    if type(sponsor) == type([]):
                        sponsor = sponsor[0]
                    if cosponsor_field in fields and bill_dictionary[cosponsor_field] not in [None, []]:
                        cosponsor = self.get_legislators(bill_dictionary[cosponsor_field])
                        for c in cosponsor:
                            edge = (sponsor, c)
                            if (sponsor, c) in attrs.keys():
                                attrs[(sponsor, c)] += " " + b
                            elif (c, sponsor) in attrs.keys():
                                attrs[(c, sponsor)] += " " + b
                            else:
                                attrs[(sponsor, c)] = b
        nx.set_edge_attributes(self.graph, attrs, "bills")
        if save_graph:
            nx.write_graphml_lxml(self.graph, self.savepath + str(chamber) + ".graphml")

    def get_bill_text(self, bill_details):
        if 'summaries' in bill_details.keys():
            summary = bill_details['summaries']
            if 'summary' in summary.keys():
                summary = summary['summary']
                if type(summary) == type([]):
                    return summary[0]['text'].lower()
                elif type(summary) == type({}):
                    return summary['text'].lower()
            else:
                summary = summary['billSummaries']
                if summary != None:
                    summary = summary['text']
                    if type(summary) == type([]):
                        return summary[0].lower()
                    else:
                        return summary.lower()
        elif 'summary' in bill_details.keys():
            summary = bill_details['summary']
            if summary != None:
                if 'text' in summary.keys():
                    return summary['text'].lower()
        return ""

    def cosponsor_metric(self, cosponsors):
        if type(cosponsors) == type({}):
            cosponsors = cosponsors['isOriginalCosponsor']
            num_cosponsors = len(cosponsors) # float(cosponsors.count('True')) # 
        else:
            num_cosponsors = len(cosponsors)
        return num_cosponsors

    def filter_nothing_bills(self, chamber, save_graph):
        bad_bills = []
        for bill in self.all_bills.keys():
            bill_details = self.all_bills[bill]
            if 'cosponsors' in bill_details.keys():
                cosponsors = bill_details['cosponsors']
                if cosponsors != None:
                    is_nothing = False
                    bill_text = self.get_bill_text(bill_details)
                    for w in self.nothing_words:
                        if w in bill_text:
                            is_nothing = True

                    if is_nothing:
                        bad_bills.append(bill)
                         
        self.filtered.add_nodes_from(self.graph.nodes(data=True))

        existing_edges = list(self.graph.edges.data())
        edges_to_add = []
        for e in existing_edges:
            edited_bills = []
            weight = 0
            if 'bills' in e[2].keys():
                bills = e[2]['bills'].split(" ")
                to_add = True
                for b in bills:
                    if b not in bad_bills:
                        edited_bills.append(b)
                        weight += 1
                if weight != 0:
                    edge = (e[0], e[1], {"weight": weight, "bills": " ".join(edited_bills)})
                    edges_to_add.append(edge)

        self.filtered.add_edges_from(edges_to_add)
                
        if save_graph:
            nx.write_graphml_lxml(self.filtered, self.savepath + str(chamber) + "_filtered.graphml")
    
    def verify_senators(self, bill_type, people_names):

        # print(people_names)
        reader = PdfReader('github_legislator_data\\senators_chronlist.pdf')
        date_format = "%B %d, %Y"
        start_of_congress = datetime.datetime.strptime("January 3, " + str(1787 + 2*self.number), date_format)
        print(start_of_congress)
        pages = [reader.pages[i] for i in range(len(reader.pages))]
        all_text = ''.join([page.extract_text() for page in pages])

        current_legs = pd.read_csv('github_legislator_data\\legislators-current.csv')
        thomas = list(current_legs['thomas_id'])
        bioguides = list(current_legs['bioguide_id'])


        for person in people_names:
            person_id = person[0]
            if person_id.isdigit(): 
                person_id = int(person_id)
            # print(person_id in thomas, person_id in bioguides, person_id not in thomas and person_id not in bioguides)
            person_details = person[1]
            name_key = ""
            if 'name' in person_details.keys():
                full_name = person_details['name']
            else:
                full_name = person_details['fullName'][5:].split(" [")[0]
            lastname = full_name.split(" ")[0]
            ind = -1
            ind = all_text.rfind(full_name)
            if ind == -1:
                ind = all_text.rfind(lastname)
            if ind == -1:
                print(person)
            else:
                # print("Looking for", full_name)
                after_str = all_text[ind:]
                try:
                    date_str = re.findall(r'[A-Z][a-z]* \d*, \d\d\d\d', after_str)[0]
                    expiration_date = datetime.datetime.strptime(date_str, date_format)
                    # print(full_name, expiration_date)
                    if start_of_congress > expiration_date and (person_id not in thomas and person_id not in bioguides):
                        print(person, expiration_date)
                except ValueError:
                    if (person_id not in thomas and person_id not in bioguides):
                        print(person, expiration_date, "---")
                    pass

    def build_bipartite_graph(self, chamber, save_graph): # after building normal graph
        t0 = time.time()
        edges = []
        self.bipartite.add_nodes_from(self.graph.nodes(data=True)) # add congresspeople
        # bill_data = [(k, self.all_bills[k]) for k in self.all_bills.keys()]

        sponsor_field = "sponsors"
        cosponsor_field = "cosponsors"
        for b in self.all_bills.keys():
            if b[0] == chamber[0]:
                self.bipartite.add_node(b)
                bill_dictionary = self.all_bills[b]
                fields = list(bill_dictionary.keys())
                if "sponsor" in fields:
                    sponsor_field = "sponsor"
                if sponsor_field in fields and bill_dictionary[sponsor_field] not in [None, []]:
                    sponsor = self.get_legislators(bill_dictionary[sponsor_field])
                    if type(sponsor) == type([]):
                        sponsor = sponsor[0]
                    if cosponsor_field in fields and bill_dictionary[cosponsor_field] not in [None, []]:
                        cosponsor = self.get_legislators(bill_dictionary[cosponsor_field])
                        if type(cosponsor) != type([]):
                            cosponsor = [cosponsor]
                        cosponsor.append(sponsor)
                        for c in cosponsor:
                            edge = (c, b)
                            edges.append(edge)
        self.bipartite.add_edges_from(edges)
        if save_graph:
            nx.write_graphml_lxml(self.bipartite, self.savepath + str(chamber) + "_bipartite.graphml")
        t1 = time.time()
        print("Bipartite built in", t1 - t0, "s")


    def build_backbone(self, chamber, save_graph):
        t0 = time.time()
        B = self.bipartite
        G = self.graph
        congresspeople_nodes = [n for n in B.nodes() if ('h' != n[0] and 's' != n[0])]
        scored = nb.sdsm(B, agent_nodes=congresspeople_nodes) #, projection="hyper"
        self.backbone = nb.threshold_filter(scored, "sdsm_pvalue", 0.05, mode="below")
        self.backbone.add_nodes_from(G.nodes(data=True))

        if save_graph:
            nx.write_graphml_lxml(self.backbone, self.savepath + str(chamber) + "_backbone.graphml")
        t1 = time.time()
        print("Backbone built in", t1 - t0, "s")

    def visualize_graph(self, G, bill_type, name_id):
        colors = {"D": "blue", "R": "red", "I": "purple"}
        parties = nx.get_node_attributes(G, "party")        
        pos = nx.circular_layout(G)

        edge_x = []
        edge_y = []
        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        node_x = []
        node_y = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines+text",
                line=dict(width=0.1, color="black"),
                hoverinfo="none",
            )
        )

        parties = [colors[i] for i in list(parties.values())]
        fig.add_trace(
            go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers",
                text=list(nx.get_node_attributes(G, name_id).values()),
                textposition="top center",
                marker=dict(size=5, color=parties),
                hoverinfo="text"
            )
        )
        print(bill_type, "# nodes:", len(G.nodes()), "# edges:", len(G.edges()))
        filetitle = "th Congress, " + bill_type
        fig.update_layout(title=str(self.number) + filetitle, showlegend=False)
        fig.write_html(self.savepath + filetitle + ".html")      


def rebuild_base_graphs(congress_num, ET,  to_verify):
    bill_types = {'house': ['hjres', 'hres', 'hr'], 'senate': ['sjres', 'sres', 's']}

    datapath = ""
    for root, dirs, files in os.walk(".\\propublica_data\\" + str(congress_num)):
        if root.endswith("bills"):
            datapath = root
            break
    individual_congress = Congress(congress_num, datapath, bill_types)
    if not to_verify:
        individual_congress.get_bills(dump=True, save_graph=True)

    for b in list(bill_types.keys()):
        print(b)
        if not to_verify:
            individual_congress.build_graph_from_adjlist(b)
            individual_congress.add_parties_from_github(b)
            individual_congress.update_bill_edges(b, True) 
            G = individual_congress.graph 
            individual_congress.verify_congresspeople(b, G.nodes.data())
            if b == 'house':
                individual_congress.add_house_predicted_ethnicities(b, ET)
                individual_congress.add_house_district_info(b, ET)

        else:
            individual_congress.build_graph_from_adjlist(b)
            individual_congress.get_from_json()

def main():
    ET = pd.read_csv("github_legislator_data\\msu_ippsr_house_data_93-117.csv")
    for congress_num in range(93, 94): #93, 118
        print(congress_num, "-")
        rebuild_base_graphs(congress_num, ET, False)
        

if __name__ == "__main__":
    main()