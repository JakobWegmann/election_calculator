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
from functions_law import zweitstimmen_by_state
from functions_law import election_of_landeslisten_2021
from functions_law import eligible_parties

if user == "Jakob":
    path = "C:/Users/jakob/sciebo/Bonn/6th_semester/election_calculator"
elif user == "Dominik":
    path = "/home/dominik/Dokumente/election_calculator"
else:
    print("No such user exists!")

# * Load the data we need. (Left as raw as possible.)
data = pd.read_json(f"{path}/bld/data/raw_data.json")

with open("../../bld/data/wahlkreis_bundeslaender.pickle", "rb") as handle:
    bundesländer_wahlkreise = pickle.load(handle)

wahlkreise = []
for bundesland in bundesländer_wahlkreise.keys():
    wahlkreise = wahlkreise + bundesländer_wahlkreise[bundesland]

# * Separating Erst- und Zweitstimmen.
erststimmen, zweitstimmen = partition_of_votes(data, wahlkreise)

# Calculation of Direktmandate
# TODO: Delete next line later.
# erststimmen = pd.read_json(f"{path}/bld/data/erststimmen.json")

# * Calculate Direktmandate.
erststimmen.set_index(["Partei"], inplace=True)

direktmandate = erststimmen.apply(direktmandate)

direktmandate_by_party = direktmandate.sum(axis=1).astype("int").copy()
direktmandate_by_party.name = "direktmandate"

# * Determine parties that are eligible.
eligible = eligible_parties(data, direktmandate_by_party)

# * Calculation of Listenplätze (first round: on Bundesländer level)
bundesländer = list(bundesländer_wahlkreise.keys())
zweitstimmenanteil_by_state = zweitstimmen_by_state(data, bundesländer)

# TODO: Delete next line later.
# zweitstimmen = pd.read_json(f"{path}/bld/data/zweitstimmen.json")
zweitstimmen.set_index(["Partei"], inplace=True)
zweitstimmen["sum by party"] = zweitstimmen.sum(axis=1).astype("int")

total_available_listenplaetze = 299

listenplätze_by_party = election_of_landeslisten_2021(
    zweitstimmen["sum by party"], total_available_listenplaetze
)
listenplätze_by_party.name = "listenplaetze"

# Calculate number of parliamentarians for each party within one Land
# (max of Direktmandate und Listenplätze)
listen_und_direktmandate = pd.concat(
    [listenplätze_by_party, direktmandate_by_party], axis=1
)
listen_und_direktmandate["minimum_num_member"] = listen_und_direktmandate.max(axis=1)


# offene Baustellen:
# TODO Relative Pfade (pytask? oder zu nervig?)
# TODO Stimmen pro Bundesland als Input (momentan gesamter Bund um Code zu testen)
# TODO Spalten: Bundesländer, Zeilen: Parteien, Zellen: Absolute Anzahl an Stimmen
# TODO      -> ist in load_data.py. Speichern, etc.?
# TODO Noch zu finden: Sitze pro Bundesland
# TODO Drop of non-eligible parties (relevant for FDP)
# TODO -> Funktion eligible_parties soll das erledigen.
