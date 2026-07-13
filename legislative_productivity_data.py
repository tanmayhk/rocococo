# existing DWG data from https://campuspress.yale.edu/davidmayhew/datasets-divided-we-govern/
# Original data from 1947-1990
# new important laws from same link, scraped here

# UPDATED FROM 1991-1992 to 2021-2022 leg. sessions

from pypdf import PdfReader
import re
import csv
import io
import pandas as pd
from statsmodels.api import add_constant, OLS
import pylatex.config as cf
from pylatex import Document, NoEscape
from pdflatex import PDFLaTeX

data_filepath = ".\\legislative_productivity\\"
OLS_filepath = ".\\OLS_tables_small_world\\"


all_fields = {"House Clustering Coeff.": "HOUSE_CC", "House Path Length": "HOUSE_PL", "House Small World $Q$": "HOUSE_Q", "Senate Clustering Coeff.": "SENATE_CC", "Senate Path Length": "SENATE_PL", "Senate Small World $Q$": "SENATE_Q"}

new_vars = ["Senate Clustering Coeff.", "Senate Path Length"]
new_fields = []
for i in new_vars:
    new_fields.append(all_fields[i])

short_title = '_'.join([''.join([j[0] for j in i.split(" ")]) for i in new_vars])
tex_doc = OLS_filepath + short_title + ".txt"

def format_session(y):
    y1 = str(y)
    y2 = str(y + 1)
    if y2[2:] == "00":
        return y1 + "-" + y2
    else:
        return y1 + "-" + y2[2:]

years = [format_session(i) for i in range(1991, 2022, 2)]

def get_N_of_LAWS(): 
    laws_dict = {i: 0 for i in years}

    # 1991-2014
    # Source: https://bpb-us-w2.wpmucdn.com/campuspress.yale.edu/dist/5/444/files/2016/06/datasets-laws-1991-2014-arnold-20f8cyy.pdf
    reader = PdfReader(data_filepath + 'datasets-laws-1991-2014-arnold-20f8cyy.pdf')
    pages = [reader.pages[i] for i in range(len(reader.pages))]
    all_text = ''.join([page.extract_text() for page in pages])
    split_text = re.split(r'(\d\d\d\d-\d\d\d\d|\d\d\d\d-\d\d)', all_text)[3:]
    for i in range(0, len(split_text), 2):
        year = split_text[i]
        text = split_text[i + 1]
        num_laws = text.count("*")
        laws_dict[year] = num_laws
    
    # 2015 to 2022, REALLY DIFFICULT TO SCRAPE
    num_laws = [12, 12, 15, 13]
    c = 0
    for year in range(2015, 2022, 2):
        session = format_session(year)
        laws_dict[session] = num_laws[c]
        c += 1
    return laws_dict

def get_budgetary(y1, y2):
    # Source: https://www.whitehouse.gov/omb/information-resources/budget/historical-tables/, Table 1.1
    budgetary_dict = {format_session(i): 0 for i in range(y1, y2, 2)}
    individual_years = [str(i) for i in range(y1, y2 + 1)]
    c = 1
    outlay = 0
    surplus_deficit = 0
    budgetary = 0
    with open(data_filepath + "budgetary.csv", "r") as f:
        data = csv.reader(f)
        for row in data:
            if row[0] in individual_years:

                year_outlay = int(row[2].replace(",", ""))
                year_surplus_deficit = int(row[3].replace(",", ""))
                if c % 2 == 1:
                    budgetary = 0
                    outlay = 0
                    surplus_deficit = 0
                budgetary += float(year_surplus_deficit/year_outlay)
                outlay += year_outlay
                surplus_deficit += year_surplus_deficit
                if c % 2 == 0:
                    budgetary = float(budgetary/2)
                    budgetary = round(budgetary*100)
                    s = format_session(int(row[0]) - 1)
                    budgetary_dict[s] = budgetary
                c += 1
    return budgetary_dict

def get_term_start():
    term_dict = {i: (3 - int(i[:4]) % 4)//2 for i in years}
    return term_dict
        
def get_UNI_DIV():
    # source: https://en.wikipedia.org/wiki/Divided_government_in_the_United_States
    uni_div_dict = {i: 0 for i in years}
    div_govt = [["1991","1993","D","D"], # Columns of table: year start, year end, senate, house
        ["1993","1995","D","D"],
        ["1995","1997","R","R"],
        ["1997","1999","R","R"],
        ["1999","2001","R","R"],
        ["2001","2003","D","R"],
        ["2003","2005","R","R"],
        ["2005","2007","R","R"],
        ["2007","2009","D","D"],
        ["2009","2011","D","D"],
        ["2011","2013","D","R"],
        ["2013","2015","D","R"],
        ["2015","2017","R","R"],
        ["2017","2019","R","R"],
        ["2019","2021","R","D"],
        ["2021","2023","D","D"]]
    for i in div_govt:
        if i[2] == i[3]:
            uni_div_dict[format_session(int(i[0]))] = 1
        else:
            uni_div_dict[format_session(int(i[0]))] = 0
    return uni_div_dict

def update_DWG_file():
    n_law_dict = get_N_of_LAWS()
    budgetary = get_budgetary(1991, 2022)
    term_dict = get_term_start()
    uni_div = get_UNI_DIV()

    with open(data_filepath + "DWG_equation.csv", "a", newline='') as f:
        data = csv.writer(f,delimiter=',')
        for i in range(1991, 2022, 2):
            session = format_session(i)
            n_laws = n_law_dict[session]
            budget = budgetary[session]
            term = term_dict[session]
            ud = uni_div[session]
            mood = 0
            data.writerow([session, n_laws, ud, term, mood, budget])
    f.close()
    
# update_DWG_file()

# -------------------------------------------------------------------
# MOSTLY DEPRECATED, MOVING TO POLARIZATION_EXPLORATIONS.PY FUNCTIONS
# -------------------------------------------------------------------

def OLS_regression(y1, y2): # Table 1 of original paper?
    ind1 = ((y1 - 1947)//2)
    ind2 = ((y2 - 1947)//2)

    data_table = pd.read_csv(data_filepath + "DWG_equation.csv") 

    X = data_table[new_fields + ['UNI/DIV','1st 1/2 term','MOOD','Budgetary']][ind1:ind2]
    # X = data_table[['UNI/DIV','1st 1/2 term','MOOD','Budgetary']][ind1:ind2]
    
    y = data_table['N of LAWS'][ind1:ind2]
    X = add_constant(X)
    est = OLS(y, X.astype(float)).fit()
    # print(y1, y2)
    # print(X)
    # # print(est.summary())
    # print("===================\n\n\n")
    return est.summary()

def to_latex(y1, y2, csv_text):
    t = csv_text.split("\n")
    # col_elements = 
    table = []
    stop = False
    for i in t:
        row = i.split(",")
        row = [r.replace(" ", "") for r in row]
        if row[0] == "Omnibus:":
            stop = True
        if not stop:
            table.append(row)
    r_squared = round(float(table[1][3]), 2)
    adj_r_squared = round(float(table[2][3]), 2)
    N = (y2 - y1 + 1)//2
    ols_results = table[10:]
    variables = len(ols_results) - 1
    col_values = ["" for i in range(2*variables + 3)]
    indices = list(range(0, 2*variables, 2))

    c = 0
    for ind in range(1, variables + 1):
        row = ols_results[ind]
        coeff = round(float(row[1]), 2)
        stderr = round(float(row[2]), 2)
        p_value = round(float(row[4]), 2)
        stat_sig = ""
        if p_value < 0.05:
            stat_sig = "^*"
        col_values[indices[ind - 1]] = "$" + str(coeff) + stat_sig + "$"
        col_values[indices[ind - 1] + 1] = "$(" + str(stderr) + ")$"
        c = indices[ind - 1] + 1
    col_values[c + 1] = str(N)
    col_values[c + 2] = str(r_squared)
    col_values[c + 3] = str(adj_r_squared)
               
    return col_values


# DEFAULT TABLE FORMAT:

# \begin{tabular}{ c } 
# \hline
#  \\
# \hline
# \hline
# Intercept \\
#  \\
# Divided Government \\
#  \\
# Start of Term \\
#  \\
# Activist Mood \\
#  \\
# Budgetary Situation \\
#  \\
# $N$ \\
# $R^2$ \\
# Adjusted $R^2$ \\
#  \hline
# \end{tabular}


def write_table(table_lines, new_col, title):
    x = table_lines[0]
    y = x.split("c")
    z = y[:len(y) - 1] + [' '] + [y[len(y) - 1]]
    new_tabular = "c".join(z)
    table_lines[0] = new_tabular

    headers = table_lines[2].replace(" \\\\\r\n", "")
    x = headers.split("&")
    x.append(" " + title)
    new_headers = "&".join(x)
    new_headers += " \\\\\r\n"
    table_lines[2] = new_headers
    # print(new_col, len(new_col))
    for i in range(len(new_col)):
        c = new_col[i]
        # print(c, table_lines[5 + i])
        existing_row = table_lines[5 + i].replace(" \\\\\r\n", "")
        x = existing_row.split("&")
        # print(c, x)
        # print("---")
        x[len(x) - 1] += " "
        x.append(" " + c)
        new_row = "&".join(x)
        new_row += " \\\\\r\n"
        table_lines[5 + i] = new_row
    return table_lines
    


def generate_OLS_tables(y1, y2, OLS_summary):
    title = str(y1) + "-" + str(y2)
    csv_text = OLS_summary.as_csv()
    # Use StringIO to treat string as a file
    data_io = io.StringIO(csv_text)
    # Read the string data
    reader = csv.reader(data_io)
    # Write to a CSV file
    with open(OLS_filepath + title + ".csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for row in reader:
            writer.writerow(row)

    latex_col = to_latex(y1, y2, csv_text)
    with open(tex_doc, "r", newline="") as f:
        tl = f.readlines()
    
    new_lines = write_table(tl, latex_col, title)
    with open(tex_doc, "w", newline="") as f:
        f.writelines(new_lines)
    
# update_DWG_file()
# y1 = 1947
# y2 = 2022

vars = ['Intercept'] + new_vars + ['Divided Government','Start of Term','Activist Mood','Budgetary Situation']
years = [(1973, 2004), (2004, 2022), (1973, 2022)]

beginning = ['\\begin{tabular}{ c } \r\n', '\\hline\r\n', ' \\\\\r\n', '\\hline\r\n', '\\hline\r\n']
end = ['$N$ \\\\\r\n', '$R^2$ \\\\\r\n', 'Adjusted $R^2$ \\\\\r\n', ' \\hline\r\n', '\\end{tabular}']

with open(tex_doc, "w", newline="") as f:
    f.writelines(beginning)
    for i in vars:
        f.writelines([i + ' \\\\\r\n', ' \\\\\r\n'])
    f.writelines(end)
f.close()

for year in years:
    y1 = year[0]
    y2 = year[1]
    print(y1, y2)
    ols_result = OLS_regression(y1, y2)
    generate_OLS_tables(y1, y2, ols_result)

