import pandas as pd
import os

user = "Dominik"

if user == "Dominik":
    os.chdir("/home/dominik/Dokumente/election_calculator/src/analysis")
else:
    pass

from functions_law import direktmandate
from functions_law import election_of_landeslisten_2021
from functions_law import eligible_parties

if user == "Jakob":
    path = "C:/Users/jakob/sciebo/Bonn/6th_semester/election_calculator"
elif user == "Dominik":
    path = "/home/dominik/Dokumente/election_calculator"
else:
    print("No such user exists!")

# Calculation of Direktmandate
erststimmen = pd.read_json(f"{path}/bld/data/erststimmen.json")

erststimmen.set_index(["Partei"], inplace=True)

direktmandate = erststimmen.apply(direktmandate)

direktmandate_by_party = direktmandate.sum(axis=1).astype("int").copy()
direktmandate_by_party.name = "direktmandate"

# Calculation of Listenplätze (first round: on Bundesländer level)
zweitstimmen = pd.read_json(f"{path}/bld/data/zweitstimmen.json")
zweitstimmen.set_index(["Partei"], inplace=True)
zweitstimmen["sum by party"] = zweitstimmen.sum(axis=1).astype("int")

zweitstimmen_prozentual = pd.read_json(f"{path}/bld/data/zweitstimmen_prozentual.json")
zweitstimmen_prozentual.drop(columns='Stimme', inplace=True)

# ! Drop non-eligible parties (5% Hürde, sum by party)
eligible_votes = eligible_parties(zweitstimmen_prozentual[["Partei", "Bundesgebiet"]], direktmandate_by_party)

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
# TODO Spalten: Bundesländer, Zeilen: Parteien, Zellen: Absolute Anzahl an Stimmen -> ist in load_data.py. Speichern, etc.?
# TODO Noch zu finden: Sitze pro Bundesland
# TODO Drop of non-eligible parties (relevant for FDP) -> Funktion eligible_parties soll das erledigen.
