import os
import pickle

import pandas as pd

user = "Dominik"

if user == "Dominik":
    os.chdir("/home/dominik/Dokumente/election_calculator/src/analysis")
else:
    pass

if user == "Jakob":
    os.chdir("C:/Users/jakob/sciebo/Bonn/6th_semester/election_calculator/src/analysis")
else:
    pass

from functions_law import partition_of_votes
from functions_law import bundestagswahl_2013_2017
from functions_law import allocation_seats_after2013

if user == "Jakob":
    path = "C:/Users/jakob/sciebo/Bonn/6th_semester/election_calculator"
elif user == "Dominik":
    path = "/home/dominik/Dokumente/election_calculator"
else:
    print("No such user exists!")

# * STEP 1: Calculate initial number of seats for each state.
population = pd.read_json(f"{path}/bld/data/population_data.json")
population.set_index(["Bundesland"], inplace=True)
population = pd.to_numeric(population["Deutsche"])
min_seats_bundestag = 598
initial_seats_by_state = allocation_seats_after2013(population, min_seats_bundestag)

# * Step 2: Calculate the number of Direktmandate.
# * Load the data we need. (Left as raw as possible.)
data = pd.read_json(f"{path}/bld/data/raw_data.json")

with open("../../bld/data/wahlkreis_bundeslaender.pickle", "rb") as handle:
    bundesländer_wahlkreise = pickle.load(handle)

wahlkreise = []
for bundesland in bundesländer_wahlkreise.keys():
    wahlkreise = wahlkreise + bundesländer_wahlkreise[bundesland]

# * Separating Erst- und Zweitstimmen.
erststimmen = partition_of_votes(data, wahlkreise)[0]
erststimmen.set_index(["Partei"], inplace=True)
bundesländer = list(bundesländer_wahlkreise.keys())
zweitstimmen_bundesland = partition_of_votes(data, bundesländer)[1]
zweitstimmen_bundesland.set_index(["Partei"], inplace=True)

zweitstimmen_bundesgebiet = (
    data[data["Stimme"] == "Zweitstimmen"].loc[:, ["Partei", "Bundesgebiet"]].copy()
)
zweitstimmen_bundesgebiet.set_index(["Partei"], inplace=True)

bts_bundesland, ausgleich_ueberhang, government = bundestagswahl_2013_2017(
    erststimmen,
    zweitstimmen_bundesland,
    zweitstimmen_bundesgebiet,
    bundesländer_wahlkreise,
    initial_seats_by_state,
)

# * Identifying marginal results with large implications
# Idea: Change Erststimmen marginally, check the effect


# offene Baustellen:
# TODO Relative Pfade (pytask? oder zu nervig?)
# TODO Stimmen pro Bundesland als Input (momentan gesamter Bund um Code zu testen)
# TODO Spalten: Bundesländer, Zeilen: Parteien, Zellen: Absolute Anzahl an Stimmen
# TODO      -> ist in load_data.py. Speichern, etc.?
# TODO Noch zu finden: Sitze pro Bundesland
# TODO Drop of non-eligible parties (relevant for FDP)
# TODO -> Funktion eligible_parties soll das erledigen.
