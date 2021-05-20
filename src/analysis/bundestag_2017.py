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

# # * Identifying marginal results with large implications
# # Idea: Change Erststimmen marginally, check the effect

# effect_changed_erststimme = pd.DataFrame(
#     0, index=erststimmen.keys(), columns=["# geänderte Sitze", "benötigte Stimmen"]
# )

# for wahlkreis in erststimmen.keys():
#     print("Wahlkreis:", wahlkreis)
#     # replace value of second largest party by value of largest party + 1
#     erststimmen_manipulated = erststimmen.copy()
#     largest_party = erststimmen_manipulated[wahlkreis].nlargest(2).index.values[0]
#     second_largest_party = (
#         erststimmen_manipulated[wahlkreis].nlargest(2).index.values[1]
#     )
#     erststimmen_manipulated.loc[second_largest_party, wahlkreis] = (
#         erststimmen_manipulated.loc[largest_party, wahlkreis] + 1
#     )
#     num_votes_manipulated = (
#         erststimmen_manipulated.loc[second_largest_party, wahlkreis]
#         - erststimmen.loc[second_largest_party, wahlkreis]
#     )

#     # Calculate results with manipulated votes
#     (
#         bts_bundesland_manipulated,
#         ausgleich_ueberhang_manipulated,
#         government_manipulated,
#     ) = bundestagswahl_2013_2017(
#         erststimmen_manipulated,
#         zweitstimmen_bundesland,
#         zweitstimmen_bundesgebiet,
#         bundesländer_wahlkreise,
#         initial_seats_by_state,
#     )

#     # Save effect size and number of necessary votes of for each Wahlkreis
#     num_changes = (bts_bundesland - bts_bundesland_manipulated).abs().sum().sum()

#     effect_changed_erststimme.loc[wahlkreis, "# geänderte Sitze"] = num_changes
#     effect_changed_erststimme.loc[
#         wahlkreis, "benötigte Stimmen"
#     ] = num_votes_manipulated

# effect_changed_erststimme.sort_values(by=["benötigte Stimmen"], inplace=True)
# effect_changed_erststimme.sort_values(
#     by=["# geänderte Sitze"], ascending=False, inplace=True, kind="mergesort"
# )

# # Analyses of most interesting result
# # ausgleich_ueberhang-ausgleich_ueberhang_manipulated


# # * Variation in Zweitstimmen
# # Relevant level is Bundesland
# # Iteratively increase and decrease number of votes for each party within each Bundesland
# # until one effect on seats appears (starting step size: 100)

# # Alternative: Check for changes within next 2000 votes, pick maximum
# # More convincing: I want to know whether chanes occur
# # DataFrame: Bundesland, changed party, number of changed votes, effect on other partys
# # Also Dictionary: Bundesland, Party, Numofvotes: save DataFrame with differences
# # Kann man Fälle über alle DataFrames im Dictionary prüfen, also bspw.
# ein Mandat mehr für Grün in BW?

# # Determine first change, then look again for other change (substract from initial DataFrame)


# my_dict = {-1: 'apple', 2: 'ball', -5: "test"}
# my_dict[535] = {"CDU": "viel", "SPD": "wenig"}

# # Ziel: Index: Partei und ansteigend/absteigend, Keys: Bundesland

# zweitstimmen_bundesland_manipulated = zweitstimmen_bundesland.copy()
# zweitstimmen_bundesgebiet_manipulated = zweitstimmen_bundesgebiet.copy()

# num_changes = 0

# factor = 4
# votes_change = 10^4
# vorzeichen = 1

# 1335

# # if change: factor - 1, and decrease votes by votes_change

# # gehe so lange hoch, bis sich eine Änderung ergibt


# [Hessen][Grünen][-2561]
# [Hessen][Grünen][418]


# [Grünen]["Hessen 418"]

# def identify_decisive_votes(vorzeichen, factor, votes_change, num_seats_changed_before,
#  max_votes_changed, zweitstimmen_bundesland_manipulated,
# zweitstimmen_bundesgebiet_manipulated):
#     """Identify necessary number of votes for a change in seats

#     Input:

#     Output:

#     """

#     print(votes_change)
#     zweitstimmen_bundesland_manipulated.loc["CDU", "Hamburg"] = (
#         zweitstimmen_bundesland_manipulated.loc["CDU", "Hamburg"] + votes_change
#     )
#     zweitstimmen_bundesgebiet_manipulated.loc["CDU"] + votes_change
#     (
#         bts_bundesland_manipulated,
#         ausgleich_ueberhang_manipulated,
#         government_manipulated,
#     ) = bundestagswahl_2013_2017(
#         erststimmen,
#         zweitstimmen_bundesland_manipulated,
#         zweitstimmen_bundesgebiet_manipulated,
#         bundesländer_wahlkreise,
#         initial_seats_by_state,
#     )

#     num_seats_changed = (bts_bundesland - bts_bundesland_manipulated).abs().sum().sum()
#     change_in_seats = num_seats_changed_before - num_seats_changed

#     if votes_change > max_votes_changed:
#         print("Max number of vote variantion reached at:", votes_change)
#         return

#     while factor > 1 & change_in_seats > 0:
#         if factor > 1:
#             if change_in_seats == 0:
#                 votes_change = votes_change + vorzeichen * 10 ^ factor
#             elif change_in_seats != 0:
#                 vorzeichen = vorzeichen*(-1)
#                 factor = factor - 1

#     elif factor == 1 & change_in_seats > 0:
#         return bts_bundesland_manipulated, ausgleich_ueberhang_manipulated,
#               government_manipulated


#     while factor > 1 & votes_change < max_votes_changed:
#         if :
#         else:
#             pass
#         identify_decisive_votes(vorzeichen, factor, votes_change, max_votes_changed,
# zweitstimmen_bundesland_manipulated, zweitstimmen_bundesgebiet_manipulated)

#     else:


# while num_changes == 0:


# bts_bundesland_manipulated - bts_bundesland

# offene Baustellen:
# TODO Relative Pfade (für pytask muss man die Pfade anpassen,
# TODO  finde ich gerade nicht sinnvoll
# TODO government as boolean
