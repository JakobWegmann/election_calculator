import os
import pickle

import pandas as pd
from src.analysis.functions_law import direktmandate, eligible_parties

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
from functions_law import bundestagswahl_2013_2017
from functions_law import allocation_seats_after2013

from functions_people import prepare_lists
from functions_people import mark_direktmandate
from functions_people import keep_eligible_parties
from functions_people import allocate_listenplaetze

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

with open("../../bld/data/bundesland_partei_listen.pickle", "rb") as handle:
    bundesland_partei_listen = pickle.load(handle)

rename_parties = {
    "CDU" : "Christlich Demokratische Union Deutschlands",
    "SPD" : "Sozialdemokratische Partei Deutschlands",
    "Grüne" : "BÜNDNIS 90/DIE GRÜNEN",
    "CSU" : "Christlich-Soziale Union in Bayern e.V.",
    "FDP" : "Freie Demokratische Partei",
    "AfD" : "Alternative für Deutschland",
}

direktmandate = erststimmen.apply(direktmandate)
direktmandate.rename(index=rename_parties, inplace=True)
zweitstimmen_bundesgebiet.rename(index=rename_parties, inplace=True)

abgeordnete_im_bundestag = prepare_lists(bundesland_partei_listen.copy())
abgeordnete_im_bundestag = mark_direktmandate(
    abgeordnete_im_bundestag,
    bundesländer_wahlkreise,
    direktmandate,
)

direktmandate["Sum"] = 0
for bundesland in bundesländer_wahlkreise.keys():
    direktmandate[bundesland] = 0
    for wahlkreis in bundesländer_wahlkreise[bundesland]:
        direktmandate[bundesland] = direktmandate[bundesland] + direktmandate[wahlkreis]
    direktmandate["Sum"] = direktmandate["Sum"] + direktmandate[bundesland]

bts_bundesland_t = bts_bundesland.T
bts_bundesland_t.rename(index=rename_parties, inplace=True)
listenplaetze_to_allocate = bts_bundesland_t - direktmandate[list(bundesländer_wahlkreise.keys())]
listenplaetze_to_allocate.fillna(0, inplace=True)
listenplaetze_to_allocate = listenplaetze_to_allocate.astype(int)

parties_eligible = eligible_parties(zweitstimmen_bundesgebiet, direktmandate["Sum"])

abgeordnete_im_bundestag = keep_eligible_parties(abgeordnete_im_bundestag, parties_eligible)

abgeordnete_im_bundestag_final = allocate_listenplaetze(
    abgeordnete_im_bundestag,
    list(bundesländer_wahlkreise.keys()),
    eligible_parties(zweitstimmen_bundesgebiet, direktmandate["Sum"]),
    listenplaetze_to_allocate,
)
effect_changed_erststimme = pd.DataFrame(
    0, index=erststimmen.keys(), columns=["# geänderte Sitze", "benötigte Stimmen"]
)

for wahlkreis in erststimmen.keys():
    print("Wahlkreis:", wahlkreis)
    # replace value of second largest party by value of largest party + 1
    erststimmen_manipulated = erststimmen.copy()
    largest_party = erststimmen_manipulated[wahlkreis].nlargest(2).index.values[0]
    second_largest_party = (
        erststimmen_manipulated[wahlkreis].nlargest(2).index.values[1]
    )
    erststimmen_manipulated.loc[second_largest_party, wahlkreis] = (
        erststimmen_manipulated.loc[largest_party, wahlkreis] + 1
    )
    num_votes_manipulated = (
        erststimmen_manipulated.loc[second_largest_party, wahlkreis]
        - erststimmen.loc[second_largest_party, wahlkreis]
    )

    # Calculate results with manipulated votes
    (
        bts_bundesland_manipulated,
        ausgleich_ueberhang_manipulated,
        government_manipulated,
    ) = bundestagswahl_2013_2017(
        erststimmen_manipulated,
        zweitstimmen_bundesland,
        zweitstimmen_bundesgebiet,
        bundesländer_wahlkreise,
        initial_seats_by_state,
    )

    # Save effect size and number of necessary votes of for each Wahlkreis
    num_changes = (bts_bundesland - bts_bundesland_manipulated).sum().abs().sum()

    effect_changed_erststimme.loc[wahlkreis, "# geänderte Sitze"] = num_changes
    effect_changed_erststimme.loc[
        wahlkreis, "benötigte Stimmen"
    ] = num_votes_manipulated

effect_changed_erststimme.sort_values(by=["benötigte Stimmen"], inplace=True)
effect_changed_erststimme.sort_values(
    by=["# geänderte Sitze"], ascending=False, inplace=True, kind="mergesort"
)

# Analyses of most interesting result
# ausgleich_ueberhang-ausgleich_ueberhang_manipulated


# * Variation in Zweitstimmen
# Relevant level is Bundesland
# Iteratively increase and decrease number of votes for each party within each Bundesland
# until one effect on seats appears (starting step size: 100)


# offene Baustellen:
# TODO Relative Pfade (pytask? oder zu nervig?)
# TODO government as boolean
