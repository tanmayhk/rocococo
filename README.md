# rocococo 
> (**ro**bust **co**ngressional **co**sponsorship **co**nnections)

**Tanmay Kulkarni, mentored by Dr. Wendy K. Tam**

*Click [here](https://1drv.ms/f/c/007f78e7bbcc7e02/IgA8s6ncDHhmSaHn2xk9HHFAAeOWHg3qQP0KmTXgKQmx3SU?e=2xQyI1) to download all .ZIP files of data.*

## About
We present a dataset, _rocococo_, with the goals of:
1. Simplifying data retrieval for United States Congress bills and legislators.
2. Providing a set of tools for constructing and analyzing sponsor-cosponsor networks using graph theory.
3. Running simple demographic analysis within these contexts.

We collate legislative information from the 93rd to 117th Congresses using a variety of distinct open-source databases (including hand-labeled data) into readable formats. Furthermore, we provide tools for analyzing Congressional interconnectedness through sponsor-cosponsor networks (including filtered and backbone versions), and bipartite bill-legislator networks.

The overall motivation for this project was to begin by cleaning up bill data from ProPublica data store and extend work done by Dr. Tam and Dr. James H. Fowler in [Legislative Success in a Small World: Social Network Analysis and the Dynamics of Congressional Legislation](https://tam.cas.vanderbilt.edu/papers/smallworld.pdf) for longer time periods and new graphs.

## Setup
1. For Python code: [Install uv](https://docs.astral.sh/uv/getting-started/installation/) and run `uv sync` in the folder.
2. Use the link above to download the various data files (see below for more details), and place them in the code folder.

## Dataset structure
The data link above consists of four .ZIP files:
1. **`propublica_data.zip` contains all the raw, downloaded data from the ProPublica data store (see below for link).** See code files section below for information on how to redownload for future updates.
2. **`github_legislator_data.zip` contains a number of other downloaded data tables (from the data sources listed in the next section).**
   - `538_data_aging_congress.csv` is from the FiveThirtyEight Congress Demographics page.
   - `budgetary.csv` collects White House data on U.S. receipts, outlays, surpluses, and deficits.
   - `congress_ethnicity.csv` collates Brookings Institute data on different ethnic groups in Congress.
   - `datasets-laws-1991-2014-arnold-20f8cyy.pdf` summarizes David Mayhew's update to his "important laws" methodology from 1991-2014.
   - `legislators-current.csv`, `legislators-current.json`, `legislators-historical.csv`, and `legislators-historical.json` are all downloaded legislator data from the United States Congress GitHub.
   - `msu_ippsr_house_data_93-117` is a subset of the CongressData House district dataset for the time interval looked at here.
   - `senators_chronlist` is an official publication by the Senate describing terms of Senators from 1789-present (used for verification).
3. **`parsed.zip` contains all the complete data files per Congress.** For a given Congress (denote their number as `NUM`):
    - `NUM_bills` and `NUM_legislators` are JSON files that contain basic info about every bill and every legislator involved in that Congress. See the United States Congress GitHub (data link below) which sources from ProPublica for full documentation on data fields.
    - `NUMhouse` and `NUMsenate` are the GraphML files for the plain sponsor-cosponsor network. In this, each main sponsor of each bill is connected to all of its cosponsors. Each vertex has a number of different data fields (ethnicity, icspr, party, title, state, name, district). The weight of the edges corresponds to the 
    - `NUMhouse_backbone` and `NUMsenate_backbone` are the GraphML files for a backbone of the original sponsor-cosponsor network using a disparity filter (_p_ < 0.05).
    - `NUMhouse_filtered` and `NUMsenate_filtered` are the GraphML files for a filtered version of the sponsor-cosponsor network, removing so-called "nothing bills" with text that contains anything in [“medal”, “commemorat-”, “renam-”, “memorial”, “condolence”, “memory”]. This removes a lot of bills with a huge number of cosponsors but very little legislative content (which would ordinarily skew the graph).
    - `NUMhouse_bipartite` and `NUMsenate_bipartite` are the GraphML files for a bipartite agent-artifact graph that connect each sponsor and cosponsor legislator to every bill they produced. This can be used for bipartite graph projection or backbone methods like SDSM-EC to create a version of a cosponsor-cosponsor network.
    - Note: for the 93rd to 112th Congresses (inclusive), we use THOMAS ID to denote each vertex, but for the 113th Congress onward, it switches to bioguide ID.
5. **`legislative_data_tables.zip` contains a number of generated CSV tables.** The graph-theoretic metrics mentioned below are clustering coefficient, average path length, density, small-world _Q_, and occasionally clustering coefficient ratio and path length ratio (against a random graph).
   - `all_congress_descriptive_stats`, `democrat_descriptive_stats`, `republican_descriptive_stats`, and `minority_metrics` collate the graph-theoretic metrics for the plain sponsor-cosponsor network, their Democrat/Republican induced subgraphs, and the minority-party subgraphs (e.g., Democratic White, Democratic Minority, Republican White, Republican Minority) for the House.
   - All files beginning with `filtered_` collect the graph-theoretic metrics on the filtered sponsor-cosponsor networks do the same for the filtered sponsor-cosponsor network.
   - `backbone_statistics` collects the basic graph-theoretic metrics for the backbone (disparity filter) sponsor-cosponsor networks.
   - `DWG_equation` collects all the binary variables and other important variables for running basic OLS regressions as per the Mayhew methodology in the book _Divided We Govern_ (see data sources for more).
  
## Code files
This repository also contains a number of different Python files for generating and manipulating data. Most are generally exploration files testing usage, but the important ones are:
- `congress.py` is the core Congress class for building and manipulating data (JSON and GraphML) from the `parsed` folder.
- `small_world_analysis.py` is the core class for all small world and graph-theoretic methods for analyzing a network or a given subgraph (built on NetworkX).
- `propublica_download.py` allows you to download the associated ProPublica data for a given Congress (to use for updating or building out this dataset for newer Congresses).

## Data sources
This dataset draws on a variety of different sources.

_For legislator and network data:_
- [ProPublica data store](https://projects.propublica.org/datastore/#congressional-data-bulk-legislation-bills) for the full set of Congress bills.
- [United States Congress GitHub](https://github.com/unitedstates/congress-legislators) for adding more details about legislators.
- [Senate publications](https://www.senate.gov/artandhistory/history/resources/pdf/chronlist.pdf) for term limits about legislators to verify the scraped data.
- [Brookings Institution](https://www.brookings.edu/articles/vital-statistics-on-congress/) data tables on the number of legislators who belong to different ethnic groups
across time.
- [CongressData](https://cspp.ippsr.msu.edu/congress/) from MSU’s Institute for Public Policy and Social Research, tracking congressional
district and House ethnicity data, for adding ethnicity/seniority/ideology (DW-NOMINATE)/age information to the graphs themselves. The holes in this data that were identified were then filled in by hand.
- [Pew Research Center analysis](https://www.pewresearch.org/short-reads/2025/01/21/119th-congress-brings-new-growth-in-racial-ethnic-diversity-to-capitol-hill/) for methodology on ethnicity analysis.
- [FiveThirtyEight's data on Congress Demographics](https://github.com/wwbrannon/538data/tree/master/congress-demographics) for information on Congressional aging.

_For other binary variables (used and unused):_
- David Mayhew’s [Divided We Govern](https://campuspress.yale.edu/davidmayhew/datasets-divided-we-govern/) datasets to investigate his important laws, extended by hand.
- [White House data tables](https://www.whitehouse.gov/omb/information-resources/budget/historical-tables/) on budgetary information.
