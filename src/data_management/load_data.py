import numpy as np
import pandas as pd
import os

user = "Dominik"

if user == "Dominik":
    os.chdir("/home/dominik/Dokumente/election_calculator/src/data_management/")
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
)


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

# * Get a list of all parties.
parteien = data.loc[:, 'Partei'].to_list()

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

# * Collect all overall results from federal states in separate dataframe.
temp = bundesländer.copy()
temp.insert(0, 'Stimme')
temp.insert(0, 'Partei')
ergebnisse_bundesländer = data[temp].copy()

# * Drop federal states from data.
data.drop(columns=bundesländer, inplace=True)

gesamt = pd.DataFrame(columns=data.columns)
gesamt.loc[0, "Partei"] = "Gesamt"
gesamt.loc[0, "Stimme"] = "Erststimmen"
gesamt.loc[1, "Partei"] = "Gesamt"
gesamt.loc[1, "Stimme"] = "Zweitstimmen"

wahlkreise = data.columns.to_list()
for item in ["Partei", "Stimme"]:
    wahlkreise.remove(item)

if len(wahlkreise) == 300:
    print("Genau 299 Wahlkreise plus Bundesgebiet vorhanden!")
else:
    print("Zu viele Wahlkreise!")

for wahlkreis in wahlkreise:
    gesamt.loc[0, wahlkreis] = (
        data[data["Stimme"] == "Erststimmen"].loc[:, wahlkreis].astype(int).sum()
    )
    gesamt.loc[1, wahlkreis] = (
        data[data["Stimme"] == "Zweitstimmen"].loc[:, wahlkreis].astype(int).sum()
    )

erststimmen = data[data["Stimme"] == "Erststimmen"].copy()

erststimmen_to_save = erststimmen.copy()
erststimmen_to_save.drop(columns=["Stimme", "Bundesgebiet"], inplace=True)
erststimmen_to_save.to_json("../../bld/data/erststimmen.json")

erststimmen.reset_index(drop=True, inplace=True)

zweitstimmen = data[data["Stimme"] == "Zweitstimmen"].copy()
zweitstimmen.reset_index(drop=True, inplace=True)


zweitstimmen_to_save = zweitstimmen.copy()
zweitstimmen_to_save.drop(columns=["Stimme", "Bundesgebiet"], inplace=True)
zweitstimmen_to_save.to_json("../../bld/data/zweitstimmen.json")

for wahlkreis in wahlkreise:
    # Erststimmen.
    divide_erststimmen = gesamt[gesamt["Stimme"] == "Erststimmen"].loc[0, wahlkreis]
    erststimmen[wahlkreis] = erststimmen[wahlkreis].astype(int).div(divide_erststimmen)

    # Zweistimmen.
    divide_zweitstimmen = gesamt[gesamt["Stimme"] == "Zweitstimmen"].loc[1, wahlkreis]
    zweitstimmen[wahlkreis] = (
        zweitstimmen[wahlkreis].astype(int).div(divide_zweitstimmen)
    )

zweitstimmen.to_json("../../bld/data/zweitstimmen_prozentual.json")

# Direktmandate nach Erststimmen
direktmandat = erststimmen.copy()
direktmandat.drop(columns=["Stimme", "Bundesgebiet"], inplace=True)

wahlkreise.remove("Bundesgebiet")
for wahlkreis in wahlkreise:
    direktmandat[wahlkreis] = direktmandat[wahlkreis] == direktmandat[wahlkreis].max()
    direktmandat[wahlkreis] = direktmandat[wahlkreis].astype(int)

direktmandat.set_index("Partei", inplace=True)
sitze_parlament = pd.DataFrame(direktmandat.sum(axis=1))
sitze_parlament.columns = ["Direktmandate"]

# Hypothetische Direktmandate
direktmandat_hyp = pd.DataFrame(zweitstimmen[["Partei", "Bundesgebiet"]].copy())
direktmandat_hyp["Bundesgebiet"] = direktmandat_hyp["Bundesgebiet"].multiply(598)

sitze_parlament["Hypothetische Direktmandate"] = direktmandat_hyp.Bundesgebiet.to_list()
sitze_parlament
direktmandat[:7]
