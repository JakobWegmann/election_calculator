import os
import pickle

import numpy as np
import pandas as pd


user = "Dominik"

if user == "Dominik":
    os.chdir("/home/dominik/Dokumente/election_calculator/src/data_management/")
else:
    pass

if user == "Jakob":
    os.chdir(
        "C:/Users/jakob/sciebo/Bonn/6th_semester/election_calculator/src/data_management"
    )
else:
    pass

# if user == "Jakob":
#     path = "C:/Users/jakob/sciebo/Bonn/6th_semester/election_calculator"
# elif user == "Dominik":
#     path = "/home/dominik/Dokumente/election_calcuator"
# else:
#     print("No such user exists!")

# data = pd.read_csv(
#     f"{path}/src/original_data/election_results/btw2017_kerg.csv",
#     sep=";",
#     skiprows=5,
#     header=None,
#     error_bad_lines=False,
# )

data = pd.read_csv(
    "../original_data/election_results/btw2017_kerg.csv",
    sep=";",
    skiprows=5,
    header=None,
    error_bad_lines=False,
    # encoding="latin1",
)
data

# * Delete unnecessary columns in two steps.
delete = ["Nr", "gehört zu", "Vorperiode"]
for item in delete:
    data = data.loc[:, ~(data == item).any()]  # Keep if no cell contains `item`
    data.columns = range(data.shape[1])  # Resets column indices to 0,1,2,...


delete = ["Wahlberechtigte", "Wähler", "Ungültige", "Gültige"]
for item in delete:
    erststimmen = data.loc[:, (data == item).any()].columns[0]
    zweitstimmen = erststimmen  # After drop the columns shifted.

    data.drop(data.columns[erststimmen], axis=1, inplace=True)
    data.drop(data.columns[zweitstimmen], axis=1, inplace=True)
    data.columns = range(data.shape[1])
data.loc[:, :7]

for i in range(1, data.shape[1], 2):
    data.loc[0, i + 1] = data.loc[0, i]
data.loc[:, :3]

data.drop(index=2, inplace=True)
data.reset_index(inplace=True, drop=True)
data = data.T

# * Drop all empty columns and rows.
zero_cols = []
for column in range(0, data.shape[1], 1):
    if data[column].isnull().all():
        zero_cols.append(column)
    else:
        pass
data.drop(columns=zero_cols, inplace=True)
data.columns = range(data.shape[1])

zero_rows = []
for row in range(0, len(data.index), 1):
    if data.loc[row, :].isnull().all():
        zero_rows.append(row)
    else:
        pass
data.drop(index=zero_rows, inplace=True)
data.columns = data.loc[0, :]
data.drop(index=0, inplace=True)
data.reset_index(drop=True, inplace=True)

data.rename(columns={"Gebiet": "Partei", np.nan: "Stimme"}, inplace=True)
data.fillna(0, inplace=True)

parteien = {
    "Christlich Demokratische Union Deutschlands": "CDU",
    "Sozialdemokratische Partei Deutschlands": "SPD",
    "Christlich-Soziale Union in Bayern e.V.": "CSU",
    "BÜNDNIS 90/DIE GRÜNEN": "Grüne",
    "Freie Demokratische Partei": "FDP",
    "Alternative für Deutschland": "AfD",
}

for partei in parteien.keys():
    data = data.replace(partei, parteien[partei])

data.to_json("../../bld/data/raw_data.json")

# * Get a list of all parties.
parteien = data.loc[:, "Partei"].to_list()

# * All federal states.
bundesländer = [
    "Bayern",
    "Baden-Württemberg",
    "Saarland",
    "Nordrhein-Westfalen",
    "Berlin",
    "Hamburg",
    "Niedersachsen",
    "Thüringen",
    "Bremen",
    "Sachsen",
    "Sachsen-Anhalt",
    "Brandenburg",
    "Rheinland-Pfalz",
    "Schleswig-Holstein",
    "Hessen",
    "Mecklenburg-Vorpommern",
]

# * Get Wahlkreise of each Bundesland in a dictionary columns.
bundesländer_col = {}
for bundesland in bundesländer:
    bundesländer_col[bundesland] = data.columns.get_loc(bundesland)

bundesländer_col["Stimme"] = 1
bundesländer_col = dict(sorted(bundesländer_col.items(), key=lambda item: item[1]))
bundesländer_wahlkreise = {}

previous_key = "Stimme"
for key in bundesländer_col:
    bundesländer_wahlkreise[key] = data.columns[
        (bundesländer_col[previous_key] + 1) : (bundesländer_col[key])
    ].tolist()
    previous_key = key
bundesländer_wahlkreise.pop("Stimme", None)  # Remove the key 'Stimme'

with open("../../bld/data/wahlkreis_bundeslaender.pickle", "wb") as handle:
    pickle.dump(bundesländer_wahlkreise, handle, protocol=pickle.HIGHEST_PROTOCOL)

# * Get population data.
data = pd.read_csv(
    "../original_data/population/bevoelkerung_2016.csv",
    sep=";",
    skiprows=5,
    header=None,
    error_bad_lines=False,
    encoding="cp1252",
)

to_drop = [
    0,
    3,
    4,
    6,
    7,
    8,
    9,
    10,
    11,
]  # by-hand selection; but no problem as format will always be the same
data.drop(columns=to_drop, inplace=True)
data.columns = range(data.shape[1])

data.loc[0, 0] = "Bundesland"
data.loc[0, 1] = "Altersgruppe"

zero_rows = []
for row in range(0, len(data.index), 1):
    if data.loc[row, :].isnull().all():
        zero_rows.append(row)
    else:
        pass
data.drop(index=zero_rows, inplace=True)
data.columns = data.loc[0, :]
data.drop(index=[0, 1], inplace=True)
data.reset_index(drop=True, inplace=True)

data = data[(data == "Insgesamt").any(axis=1)]
data.drop(columns=["Altersgruppe"], inplace=True)
data.reset_index(drop=True, inplace=True)

data.to_json("../../bld/data/population_data.json")

# * Get Bewerber data.
data = pd.read_csv(
    "../original_data/candidates/btw2017bewerb_gewaehlt.csv",
    sep=";",
    skiprows=7,
    header=0,
    error_bad_lines=False,
    encoding="cp1252",
)

data["Bundesland"] = data["Wahlkreis_Land"]
data["Bundesland"].fillna(data["Liste_Land"], inplace=True)

rename_dict = {
    "BY" : "Bayern",
    "BW" : "Baden-Württemberg",
    "SL" : "Saarland",
    "NW" : "Nordrhein-Westfalen",
    "BE" : "Berlin",
    "HH" : "Hamburg",
    "NI" : "Niedersachsen",
    "TH" : "Thüringen",
    "HB" : "Bremen",
    "SN" : "Sachsen",
    "ST" : "Sachsen-Anhalt",
    "BB" : "Brandenburg",
    "RP" : "Rheinland-Pfalz",
    "SH" : "Schleswig-Holstein",
    "HE" : "Hessen",
    "MV" : "Mecklenburg-Vorpommern",
}

data["Bundesland"].replace(rename_dict, inplace=True)
data["Partei"] = data["Wahlkreis_ParteiBez"]
data["Partei"].fillna(data["Liste_ParteiBez"], inplace=True)
dict = {}


for bundesland in list(set(data["Bundesland"].tolist())):
    bundesland_df = data[data["Bundesland"] == bundesland].copy()
    key_value = {}
    for partei in list(set(bundesland_df["Partei"].tolist())):
        key_value[partei] = bundesland_df[bundesland_df["Partei"] == partei].copy()
        key_value[partei].drop(
            columns=[
                "Wahlkreis_Land",
                "Wahlkreis_ParteiBez",
                "Wahlkreis_ParteiKurzBez", 
                "Liste_Land",
                "Liste_ParteiBez", 
                "Liste_ParteiKurzBez",
                "Bundesland", 
                "Partei",
            ], 
            inplace=True,
        )
        key_value[partei].sort_values(by=["Liste_Platz"], inplace=True)
        key_value[partei].reset_index(inplace=True, drop=True)
    dict[bundesland] = key_value

with open("../../bld/data/bundesland_partei_listen.pickle", "wb") as handle:
    pickle.dump(dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

# * Get Wahlkreise data.
data = pd.read_csv(
    "../original_data/wahlkreise_info/20170228_BTW17_WKr_Gemeinden_ASCII.csv",
    sep=";",
    skiprows=7,
    header=0,
    error_bad_lines=False,
    encoding="cp1252",
)

data.drop(columns=["Wahlkreis-von", "Wahlkreis-bis", "PLZ-mehrere"], inplace=True)
data["Gemeindename"] = [s.split(", ", 1)[0] for s in data["Gemeindename"].tolist()]

dict = {}
for index in range(len(data["Gemeindename"].tolist())):
    dict[data["Gemeindename"].iloc[index]] = data["Wahlkreis-Bez"].iloc[index]

with open("../../bld/data/gemeinde_wahlkreis_listen.pickle", "wb") as handle:
    pickle.dump(dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
