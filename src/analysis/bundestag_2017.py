import math
import os
import pickle

import pandas as pd

user = "Jakob"

if user == "Dominik":
    os.chdir("/home/dominik/Dokumente/election_calculator/src/analysis")
else:
    pass

if user == "Jakob":
    os.chdir("C:/Users/jakob/sciebo/Bonn/6th_semester/election_calculator/src/analysis")
else:
    pass

from functions_law import partition_of_votes
from functions_law import direktmandate
from functions_law import allocation_seats_after2013
from functions_law import eligible_parties
from functions_law import last_allocation_seats

# from functions_law import sainte_lague

# from functions_law import size_bundestag

# from functions_law import redistribution_bundestag_seats

if user == "Jakob":
    path = "C:/Users/jakob/sciebo/Bonn/6th_semester/election_calculator"
elif user == "Dominik":
    path = "/home/dominik/Dokumente/election_calculator"
else:
    print("No such user exists!")

# * STEP 1: Calculate initial number of seats for each state.
population = pd.read_json(f"{path}/bld/data/population_data.json")
population.set_index(["Bundesland"], inplace=True)
# ! Only 25% sure what I´m doing
population = pd.to_numeric(population["Deutsche"])
min_seats_bundestag = 598
initial_seats_by_state = allocation_seats_after2013(population, min_seats_bundestag)

# prelim_divisor = population.sum() / 598
# initial_seats_by_state, final_divisor = sainte_lague(
#     prelim_divisor, population, int(598)
# )

# * Step 2: Calculate the number of Direktmandate.
# * Load the data we need. (Left as raw as possible.)
data = pd.read_json(f"{path}/bld/data/raw_data.json")

with open("../../bld/data/wahlkreis_bundeslaender.pickle", "rb") as handle:
    bundesländer_wahlkreise = pickle.load(handle)

wahlkreise = []
for bundesland in bundesländer_wahlkreise.keys():
    wahlkreise = wahlkreise + bundesländer_wahlkreise[bundesland]

# * Separating Erst- und Zweitstimmen.
erststimmen, zweitstimmen = partition_of_votes(data, wahlkreise)

# * Calculate Direktmandate.
erststimmen.set_index(["Partei"], inplace=True)

direktmandate_wahlkreis = erststimmen.apply(direktmandate)

direktmandate_bundesland = pd.DataFrame(
    0, index=erststimmen.index, columns=bundesländer_wahlkreise.keys()
)

for bundesland in bundesländer_wahlkreise.keys():
    direktmandate_bundesland[bundesland] = direktmandate_wahlkreis[
        bundesländer_wahlkreise[bundesland]
    ].sum(axis=1)


# * STEP 3: Calculate the Mindestsitzzahl for each federal state.
# * Calculation of Listenplätze (first round: on Bundesländer level)

# Determine parties that are eligible.
eligible = eligible_parties(data, direktmandate_bundesland.sum(axis=1))

bundesländer = list(bundesländer_wahlkreise.keys())
zweitstimmen_bundesland = partition_of_votes(data, bundesländer)[1]
zweitstimmen_bundesland.set_index(["Partei"], inplace=True)

# Keep eligible parties
zweitstimmen_bundesland = zweitstimmen_bundesland.loc[eligible]

listenplätze_bundesland = pd.DataFrame(
    index=zweitstimmen_bundesland.index, columns=zweitstimmen_bundesland.columns
)

for bundesland in bundesländer_wahlkreise.keys():
    # Listenplätze
    print("Bundsland:", bundesland)
    listenplätze_bundesland[bundesland] = allocation_seats_after2013(
        zweitstimmen_bundesland[bundesland], initial_seats_by_state.loc[bundesland]
    )


# * Calculate number of seats before Ausgleichsmandate

mindestsitzzahl = pd.DataFrame(index=eligible, columns=bundesländer)

# temp = list(set(direktmandate_bundesland.index.tolist()) - set(eligible))
# listenplätze_bundesland.loc[temp] = 0
for bundesland in bundesländer:
    for partei in eligible:
        mindestsitzzahl.loc[partei, bundesland] = max(
            listenplätze_bundesland.loc[partei, bundesland],
            direktmandate_bundesland.loc[partei, bundesland],
        )
mindestsitzzahl.index.rename("Partei", inplace=True)
mindestsitzzahl["sum_sitze"] = mindestsitzzahl.sum(axis=1)

# * Number of Ausgleichsmandate (eventual size of Bundestag)
zweitstimmen_bundesgebiet = partition_of_votes(data, ["Bundesgebiet"])[1]
zweitstimmen_bundesgebiet.set_index(["Partei"], inplace=True)
zweitstimmen_bundesgebiet.columns = ["Zweitstimmen"]
# Keep eligible parties
zweitstimmen_bundesgebiet = zweitstimmen_bundesgebiet.loc[eligible]

bundestag_seats_by_party = zweitstimmen_bundesgebiet.join(mindestsitzzahl)
bundestag_seats_by_party["divisor"] = (
    bundestag_seats_by_party["Zweitstimmen"] / bundestag_seats_by_party["sum_sitze"]
)
min_divisor = bundestag_seats_by_party["divisor"].min()
bundestag_seats_by_party["seats_unrounded"] = (
    bundestag_seats_by_party["Zweitstimmen"] / min_divisor
)
bundestag_seats_by_party["seats_rounded"] = bundestag_seats_by_party[
    "seats_unrounded"
].round(0)

# * Redistribution of additional seats to Länder

zweitstimmen_bundesland_t = zweitstimmen_bundesland.T

bundestagssitze_bundesland = pd.DataFrame(
    index=zweitstimmen_bundesland_t.index, columns=zweitstimmen_bundesland_t.columns
)

direktmandate_bundesland_t = direktmandate_bundesland.T
direktmandate_bundesland_t = direktmandate_bundesland_t[eligible]

for partei in zweitstimmen_bundesland_t.keys():
    print(partei)
    # Bundestagssitze by Land
    bundestagssitze_bundesland[partei] = last_allocation_seats(
        zweitstimmen_bundesland_t[partei],
        bundestag_seats_by_party.loc[partei, "seats_rounded"],
        direktmandate_bundesland_t[partei],
    )

# * Possible coalitions

coalitions = {
    "groko": [
        "CDU",
        "CSU",
        "SPD",
    ],
    "rot_grün": ["SPD", "Grüne"],
    "ampel": [
        "SPD",
        "Grüne",
        "FDP",
    ],
    "rot_rot_grün": [
        "SPD",
        "Grüne",
        "DIE LINKE",
    ],
    "schwarz_gelb": [
        "CDU",
        "CSU",
        "FDP",
    ],
    "Jamaika": [
        "CDU",
        "CSU",
        "Grüne",
        "FDP",
    ],
}

possible_coalition = pd.DataFrame(
    coalitions,
    index=coalitions.keys(),
    columns=["possible coalition", "sum_seats", "margin"],
)

for posble_coalitions in coalitions.keys():
    sum_seats_coalition = 0
    for partei in coalitions[posble_coalitions]:
        sum_seats_coalition = (
            sum_seats_coalition + bundestag_seats_by_party.loc[partei, "seats_rounded"]
        )
    possible_coalition.loc[posble_coalitions, "sum_seats"] = sum_seats_coalition

necc_votes_maj = math.ceil(bundestag_seats_by_party["seats_rounded"].sum() / 2)
possible_coalition["margin"] = possible_coalition["sum_seats"] - necc_votes_maj
possible_coalition["possible coalition"] = possible_coalition["margin"].apply(
    lambda x: "possible" if x >= 0 else "not possible"
)

# offene Baustellen:
# TODO Relative Pfade (pytask? oder zu nervig?)
# TODO Stimmen pro Bundesland als Input (momentan gesamter Bund um Code zu testen)
# TODO Spalten: Bundesländer, Zeilen: Parteien, Zellen: Absolute Anzahl an Stimmen
# TODO      -> ist in load_data.py. Speichern, etc.?
# TODO Noch zu finden: Sitze pro Bundesland
# TODO Drop of non-eligible parties (relevant for FDP)
# TODO -> Funktion eligible_parties soll das erledigen.
