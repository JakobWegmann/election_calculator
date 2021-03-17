import pandas as pd

user = "Jakob"

if user == "Jakob":
    path = "C:/Users/jakob/sciebo/Bonn/6th_semester/election_calculator"
elif user == "Dominik":
    path = "/home/dominik/Dokumente/election_calcuator"
else:
    print("No such user exists!")


def direktmandate(votes_by_party):
    """Determine party that wins Direktmandat

    Input:
    votes_by_party (DataFrame): By party the number of votes

    Output:
    direktmandat(DataFrame): Indicates that party that wins Direktmandat
    """

    direktmandat = votes_by_party == votes_by_party.max()
    direktmandat = direktmandat.astype(int)
    return direktmandat


erststimmen = pd.read_json(f"{path}/bld/data/erststimmen.json")

erststimmen.set_index(["Partei"])

direktmandate = erststimmen.apply(direktmandate)
