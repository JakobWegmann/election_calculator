import pandas as pd
from functions_law import direktmandate

# from functions_law import election_of_landeslisten_2021

user = "Jakob"

if user == "Jakob":
    path = "C:/Users/jakob/sciebo/Bonn/6th_semester/election_calculator"
elif user == "Dominik":
    path = "/home/dominik/Dokumente/election_calcuator"
else:
    print("No such user exists!")

erststimmen = pd.read_json(f"{path}/bld/data/erststimmen.json")

erststimmen.set_index(["Partei"], inplace=True)

direktmandate = erststimmen.apply(direktmandate)

direktmandate["sum by party"] = direktmandate.sum(axis=1).astype("int")

# Drop non-eligible parties (5% Hürde, sum by party)
# Not implemented yet


total_available_listenplaetze = 298
# zweitstimmen

# election_of_landeslisten_2021(zweitstimmen, total_available_listenplaetze)
