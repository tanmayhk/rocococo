import os
import xmltodict
import json
import networkx as nx
import plotly.graph_objects as go
import time
import csv
from pypdf import PdfReader
import datetime
import re
import pandas as pd


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

    def get_bills(self, dump=False, save_graph=False):
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
    
    def verify_congresspeople(self, bill_type, people_names):
        name_dict = {}
        state_dict = {}
        title_dict = {}
        party_dict = {}

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
                            for term in l['terms']:
                                start = datetime.datetime.strptime(term['start'], date_format2)
                                end = datetime.datetime.strptime(term['end'], date_format2)
                                if (start <= start_of_congress and end >= start_of_congress) or (start >= start_of_congress and start <= end_of_congress):
                                    if 'name' not in person_details.keys() and 'fullName' not in person_details.keys():
                                        full_name = l['name']['last'] + ", " + l['name']['first']
                                        if 'middle' in l['name'].keys():
                                            full_name += l['name']['middle'][0] + "."
                                        if 'suffix' in l['name'].keys():
                                            full_name += l['name']['suffix'][0] + "."
                                        name_dict[person_id] = full_name
                                    if 'party' not in person_details.keys():
                                        party_dict[person_id] = term['party'][0]
                                    if 'state' not in person_details.keys():
                                        state_dict[person_id] = term['state']
                                    if 'title' not in person_details.keys():
                                        title_dict[person_id] = term['type'].capitalize()
                                    to_print = False
                                    break
                    if to_print:
                        print(person_details, reason)
                        
        t1 = time.time()
        print(t1 - t0, "s")
        nx.set_node_attributes(self.graph, name_dict, "name")
        nx.set_node_attributes(self.graph, state_dict, "state")
        nx.set_node_attributes(self.graph, title_dict, "title")
        nx.set_node_attributes(self.graph, party_dict, "party")

        nx.write_graphml_lxml(self.graph, self.savepath + str(bill_type) + ".graphml")

    
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


def main():
    for congress_num in range(116, 117):
        t0 = time.time()
        bill_types = {'senate': ['sjres', 'sres', 's'], 'house': ['hjres', 'hres', 'hr']}
        datapath = ""
        for root, dirs, files in os.walk(".\\propublica_data\\" + str(congress_num)):
            if root.endswith("bills"):
                datapath = root
                break
        print(datapath)

        # bill_types = {'senate': ['sjres'], 'house': []}
        # individual_congress = Congress(93, r".\propublica_data\93\bills", bill_types)

        individual_congress = Congress(congress_num, datapath, bill_types)
        is_xml = individual_congress.get_bills(dump=True, save_graph=True)
        # individual_congress.get_from_json()
        # for b in list(bill_types.keys()):
        #     individual_congress.build_graph_from_adjlist(b)
        #     if is_xml:
        #         individual_congress.visualize_graph(b, 'fullName')
        #     else:
        #         individual_congress.visualize_graph(b, 'name')
        t1 = time.time()
        print("TOTAL TIME for", congress_num, "=", t1 - t0, "seconds")



if __name__ == "__main__":
    main()