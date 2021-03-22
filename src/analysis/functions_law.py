"""Implementation of current law that translates votes into seats in parliament
Bundeswahlgesetz §6

https://www.gesetze-im-internet.de/bwahlg/__6.html
https://www.bundestagswahl-bw.de/sitzberechnung-btw#c31948
Calculation follows
Heft 3. Endgültige Ergebnisse nach Wahlkreisen

"""
import pandas as pd


def partition_of_votes(raw_data, wahlkreise):
    """Partition the raw data into "Erststimmen" und "Zweitstimmen".

    Input:
    raw_data (DataFrame): cleaned election data
    wahlkreise (list): list with all Wahlkreise

    Output:
    erststimmen (DataFrame): By party the number of Erststimmen in each Wahlkreis
    zweitimmen (DataFrame): By party the number of Zweitstimmen in each Wahlkreis

    """

    column_names = ["Partei"] + wahlkreise
    erststimmen = (
        raw_data[raw_data["Stimme"] == "Erststimmen"].loc[:, column_names].copy()
    )
    zweitstimmen = (
        raw_data[raw_data["Stimme"] == "Zweitstimmen"].loc[:, column_names].copy()
    )

    return erststimmen, zweitstimmen


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


def eligible_parties(data, direktmandate):
    """Determine which parties reach the Bundestag in a federal state.

    Input:
    data (DataFrame): cleaned data
    direktmandate (DataFrame): By party the number of Direktmandate

    Output:
    eligible_parties (list): all parties that are eligible for BT seats
    """

    bundesgebiet = (
        data[data["Stimme"] == "Zweitstimmen"].loc[:, ["Partei", "Bundesgebiet"]].copy()
    )
    bundesgebiet.set_index(["Partei"], inplace=True)
    bundesgebiet = bundesgebiet.div(bundesgebiet.sum(axis=0))
    bundesgebiet.reset_index(inplace=True)

    eligible_direktmandate = direktmandate[direktmandate > 3].index.tolist()
    eligible_huerde = (
        bundesgebiet[bundesgebiet["Bundesgebiet"] > 0.05].loc[:, "Partei"].tolist()
    )

    eligible_parties = list(dict.fromkeys(eligible_direktmandate + eligible_huerde))

    return eligible_parties


def zweitstimmenanteil_by_state(data, bundesländer):
    """Determine the number of Bundestag seats by party for each federal state.

    Input:
    data (DataFrame): cleaned data
    bundesländer (list): list of federal states

    Output:
    bt_seats_by_state (DataFrame): By party the number of BT seats in each Bundesland

    """

    column_names = ["Partei"] + bundesländer
    zweitstimmen_by_state = (
        data[data["Stimme"] == "Zweitstimmen"].loc[:, column_names].copy()
    )
    zweitstimmen_by_state.set_index(["Partei"], inplace=True)
    zweitstimmen_by_state = zweitstimmen_by_state.div(zweitstimmen_by_state.sum(axis=0))

    return zweitstimmen_by_state


def core_sainte_lague(preliminary_divisor, data):
    """ Core of sainte_lague fucntion

    Input:
    preliminary_divisor (float): Guess for the divisor
    data (DateFrame): data processed with divisors (e.g. votes by party)

    Output:
    allocated_seats (DataFrame): number of seats by party, state, etc.
    sum_of_Seats: total number of seats
    
    """

    # Jede Landesliste (jedes Bundesland) erhält so viele Sitze, wie sich nach Teilung der Summe
    # ihrer erhaltenen Zweitstimmen (der Bevölkerung) durch einen Zuteilungsdivisor ergeben.
    allocated_seats = data.divide(preliminary_divisor).copy()

    # "Zahlenbruchteile unter 0,5 werden auf die darunter liegende ganze Zahl abgerundet,
    #  solche über 0,5 werden auf die darüber liegende ganze Zahl aufgerundet. "
    allocated_seats = allocated_seats.round(0).astype(int)

    # Calculate sum of listenplaetze after first iteration
    sum_of_seats = allocated_seats.sum()[0]

    return allocated_seats, sum_of_seats


def sainte_lague(preliminary_divisor, data, total_available_seats):
    """Iterative Sainte-Lague procedure which applies core_sainte_lague

    Input:
    preliminary_divisor (float): Guess for the divisor
    data (DateFrame): data processed with divisors (e.g. votes by party)
    total_available_seats (int): number of seats in parliament for the
        respective Bundesland, Germany, etc.

    Output:
    allocated_seats (DataFrame): seats by party, state, etc.

    """

    allocated_seats, sum_of_seats = core_sainte_lague(preliminary_divisor, data)

    while sum_of_seats > total_available_seats:
        preliminary_divisor = preliminary_divisor + 50
        allocated_seats, sum_of_seats = core_sainte_lague(preliminary_divisor, data)
    else:
        return allocated_seats, preliminary_divisor


def election_of_landeslisten_2021(zweitstimmen_by_party, total_available_listenplaetze):
    """Implementation of Bundeswahlgesetz
    § 6 Wahl nach Landeslisten (2021) Absatz 1 und 2

    Input:
    zweitstimmen_by_party(DataFrame): by party Zweitstimmen within a Bundesland
        of eligible parties
    total_available_listenplaetze(int): number of seats in parliament for the
        respective Bundesland (depends on population, is published)

    Output:
    parliamentarians_before_ausgleichsmandate(DataFrame):
    """

    # Use Sainte-Lague Zuteilungsdivisor to calculate seats by party
    #   Der Zuteilungsdivisor ist so zu bestimmen, dass insgesamt so viele
    #   Sitze auf die Landeslisten entfallen, wie Sitze zu vergeben sind.
    #   Dazu wird zunächst die Gesamtzahl der Zweitstimmen aller zu berücksichtigenden
    #   Landeslisten durch die Zahl der jeweils nach Absatz 1 Satz 3
    #   verbleibenden Sitze geteilt.

    preliminary_divisor = zweitstimmen_by_party.sum() / total_available_listenplaetze

    landesliste_before_ausgleichsmandate = sainte_lague(
        preliminary_divisor, zweitstimmen_by_party, total_available_listenplaetze
    )

    # Entfallen danach mehr Sitze auf die Landeslisten, als Sitze zu vergeben sind,
    #   ist der Zuteilungsdivisor so HERAUFZUSETZEN, dass sich bei der Berechnung
    #   die zu vergebende Sitzzahl ergibt; entfallen zu wenig Sitze auf die Landeslisten,
    #   ist der Zuteilungsdivisor entsprechend herunterzusetzen.

    return landesliste_before_ausgleichsmandate


def size_bundestag(zweitstimmen_by_party_total, minimum_members_by_land_and_party):
    """Following Heft 3. Endgültige Ergebnisse nach Wahlkreisen (2017) p.414

    Input:
    zweitstimmen_by_party_total(DataFrame): By party Zweitstimmen (Bundesrepublik)
    minimum_members_by_land_and_party(DataFrame): By party and Land
        number of minimum seats

    Output:
    bundestag_seats_by_party(DataFrame):
    """

    minimum_members_by_land_and_party[
        "sum_seats"
    ] = minimum_members_by_land_and_party.sum(axis=1)
    minimum_members_by_land_and_party["sum_seats_min_0_5"] = (
        minimum_members_by_land_and_party["sum_seats"] - 0.5
    )
    bundestag_seats_by_party = pd.concat(
        minimum_members_by_land_and_party["sum_seats_min_0_5"],
        zweitstimmen_by_party_total,
        axis=1,
    )
    bundestag_seats_by_party["divisor"] = (
        bundestag_seats_by_party["zweitstimmen"] / bundestag_seats_by_party["sum_seats"]
    )
    min_divisor = bundestag_seats_by_party["divisor"].min()
    bundestag_seats_by_party["seats_unrounded"] = (
        bundestag_seats_by_party["zweitstimmen"] / min_divisor
    )
    bundestag_seats_by_party["seats_rounded"] = bundestag_seats_by_party[
        "seats_unrounded"
    ].round(0)
    return bundestag_seats_by_party["seats_rounded"]


def redistribution_bundestag_seats(
    zweitstimmen_for_party_by_land, bundestag_seats_for_party
):
    """Following Heft 3. Endgültige Ergebnisse nach Wahlkreisen (2017) p.415 ff.

    Input:
    zweitstimmen_for_party_by_land(DataFrame): By Land Zweitstimmen for the respective party
    bundestag_seats_for_party(int): Bundestag seats for the respective party

    Output:
    seats_by_land(DataFrame): Bundestag seats by Land for the respective party:
    """

    sum_votes = zweitstimmen_for_party_by_land["zweitstimmen"].sum(axis=0)
    divisor = sum_votes / bundestag_seats_for_party
    zweitstimmen_for_party_by_land["seats_unrounded"] = (
        zweitstimmen_for_party_by_land["zweitstimmen"] / divisor
    )
    zweitstimmen_for_party_by_land["seats_rounded"] = zweitstimmen_for_party_by_land[
        "seats_unrounded"
    ].round(0)

    return zweitstimmen_for_party_by_land["seats_rounded"]
