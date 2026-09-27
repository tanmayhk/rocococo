import pandas as pd
import statistics

table = pd.read_csv("C:\\Users\\Tanmay\\git-projects\\rocococo\\github_legislator_data\\538_data_aging_congress.csv")

house = {i:[0, 0] for i in range(93, 118)}
senate = {i:[0, 0] for i in range(93, 118)}


for i in range(len(table)):
    congress = int(table["congress"][i])
    if congress >= 93 and congress < 118:
        if table["chamber"][i] == "House":
            house[congress][1] += 1
            if table["age_years"][i] >= 60:
                house[congress][0] += 1
        else:
            senate[congress][1] += 1
            if table["age_years"][i] >= 60:
                senate[congress][0] += 1
            
hmax = 58.2751540041068*3.7
smax = 64.2819986310746*9


for i in range(93, 118):
    print(house[i][0]/house[i][1])

print("")
for i in range(93, 118):
    print(senate[i][0]/senate[i][1])


