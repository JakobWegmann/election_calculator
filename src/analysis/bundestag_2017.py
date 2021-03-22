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
from functions_law import election_of_landeslisten_2021
from functions_law import eligible_parties
from functions_law import sainte_lague

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
prelim_divisor = population.sum() / 598
initial_seats_by_state, final_divisor = sainte_lague(
    prelim_divisor, population, int(598)
)

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

direktmandate = erststimmen.apply(direktmandate)

direktmandate_by_party = direktmandate.sum(axis=1).astype("int").copy()
direktmandate_by_party.name = "direktmandate"

# * Determine parties that are eligible.
eligible = eligible_parties(data, direktmandate_by_party)

# * STEP 3: Calculate the Mindestsitzzahl for each federal state.
# * Calculation of Listenplätze (first round: on Bundesländer level)
bundesländer = list(bundesländer_wahlkreise.keys())

zweitstimmen_bundesland = partition_of_votes(data, bundesländer)[1]
zweitstimmen_bundesland.set_index(["Partei"], inplace=True)

for bundesland in bundesländer_wahlkreise.keys():
    listenplätze_by_party, final_divisor = election_of_landeslisten_2021(
        zweitstimmen_bundesland[bundesland], initial_seats_by_state.loc[bundesland]
    )

listenplätze_by_party.name = "listenplaetze"

# Calculate number of parliamentarians for each party within one Land
# (max of Direktmandate und Listenplätze)
# listen_und_direktmandate = pd.concat(
#     [listenplätze_by_party, direktmandate_by_party], axis=1
# )

zweitstimmen_bundesgebiet = partition_of_votes(data, ["Bundesgebiet"])[1]


# listen_und_direktmandate["minimum_num_member"] = listen_und_direktmandate.max(axis=1)

# # Calculate number of seats before Ausgleichsmandate

# bundestag_seats_by_party = size_bundestag(
#     zweitstimmen_by_party_total, minimum_members_by_land_and_party
# )

# Ausgleichsmandate


# offene Baustellen:
# TODO Relative Pfade (pytask? oder zu nervig?)
# TODO Stimmen pro Bundesland als Input (momentan gesamter Bund um Code zu testen)
# TODO Spalten: Bundesländer, Zeilen: Parteien, Zellen: Absolute Anzahl an Stimmen
# TODO      -> ist in load_data.py. Speichern, etc.?
# TODO Noch zu finden: Sitze pro Bundesland
# TODO Drop of non-eligible parties (relevant for FDP)
# TODO -> Funktion eligible_parties soll das erledigen.
