"""Implementation of current law that translates votes into seats in parliament
Bundeswahlgesetz §6

https://www.gesetze-im-internet.de/bwahlg/__6.html
https://www.bundestagswahl-bw.de/sitzberechnung-btw#c31948
Calculation follows
Heft 3. Endgültige Ergebnisse nach Wahlkreisen

"""
import math

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


def eligible_parties(zweitstimmen_bundesgebiet, direktmandate):
    """Determine which parties reach the Bundestag in a federal state.

    Input:
    zweitstimmen_bundesgebiet (DataFrame): votes by party bundesgebiet
    direktmandate (DataFrame): By party the number of Direktmandate

    Output:
    eligible_parties (list): all parties that are eligible for BT seats
    """

    zweitstimmen_bundesgebiet = zweitstimmen_bundesgebiet.div(
        zweitstimmen_bundesgebiet.sum(axis=0)
    )
    zweitstimmen_bundesgebiet.reset_index(inplace=True)

    eligible_direktmandate = direktmandate[direktmandate > 3].index.tolist()
    eligible_huerde = (
        zweitstimmen_bundesgebiet[zweitstimmen_bundesgebiet["Bundesgebiet"] > 0.05]
        .loc[:, "Partei"]
        .tolist()
    )

    eligible_parties = list(dict.fromkeys(eligible_direktmandate + eligible_huerde))

    return eligible_parties


def core_sainte_lague(preliminary_divisor, data):
    """Core of sainte_lague fucntion

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
    sum_of_seats = allocated_seats.sum()

    return allocated_seats, sum_of_seats


def sainte_lague(preliminary_divisor, data, total_available_seats):
    """Iterative Sainte-Lague procedure which applies core_sainte_lague

    Input:
    preliminary_divisor (float): Guess for the divisor
    data (pd.DateFrame): data processed with divisors (e.g. votes by party)
    total_available_seats (int): number of seats in parliament for the
        respective Bundesland, Germany, etc.

    Output:
    allocated_seats (DataFrame): seats by party, state, etc.

    """

    allocated_seats, sum_of_seats = core_sainte_lague(preliminary_divisor, data)

    while sum_of_seats != total_available_seats:
        if sum_of_seats > total_available_seats:
            preliminary_divisor = preliminary_divisor + 50
        elif sum_of_seats < total_available_seats:
            preliminary_divisor = preliminary_divisor - 50
        else:
            pass

        print("Sum of seats:", sum_of_seats)
        print("Total available seats:", total_available_seats)
        print("Divisor:", preliminary_divisor)
        allocated_seats, sum_of_seats = core_sainte_lague(preliminary_divisor, data)
    else:
        return allocated_seats, preliminary_divisor


def sainte_lague_new(preliminary_divisor, data, available_seats):
    """Iterative Sainte-Lague procedure which applies core_sainte_lague

    Input:
    preliminary_divisor (float): Guess for the divisor
    data (pd.DateFrame): data processed with divisors (e.g. votes by party)
    available_seats (int): number of seats to be allocated

    Output:
    allocated_seats (pd.DataFrame): seats allocated by party, state, etc.

    """

    # Jede Landesliste (jedes Bundesland) erhält so viele Sitze, wie sich nach Teilung der Summe
    # ihrer erhaltenen Zweitstimmen (der Bevölkerung) durch einen Zuteilungsdivisor ergeben.
    allocated_seats = data.divide(preliminary_divisor).copy()
    # "Zahlenbruchteile unter 0,5 werden auf die darunter liegende ganze Zahl abgerundet,
    #  solche über 0,5 werden auf die darüber liegende ganze Zahl aufgerundet. "
    allocated_seats = allocated_seats.round(0).astype(int)

    # Calculate sum of listenplaetze after first iteration
    sum_of_seats = allocated_seats.sum()

    if sum_of_seats != available_seats:
        if sum_of_seats > available_seats:
            preliminary_divisor = preliminary_divisor + 50
        elif sum_of_seats < available_seats:
            preliminary_divisor = preliminary_divisor - 50
        allocated_seats = sainte_lague_new(preliminary_divisor, data, available_seats)

    return allocated_seats


def allocation_seats_after2013(zweitstimmen_by_party, available_seats):
    """Implementation of Bundeswahlgesetz
    § 6 Wahl nach Landeslisten (2021) Absatz 1 und 2,
    Heft 3. Endgültige Ergebnisse nach Wahlkreisen (2017) p. 398
    describes the procedure a bit different

    Input:
    zweitstimmen_by_party (pd.DataFrame): Zweitstimmen by party
    available_seats (int): number of seats available

    Output:
    allocation_of_seats (pd.DataFrame): allocation of seats by entity
    """

    # Use Sainte-Lague Zuteilungsdivisor to calculate seats by party
    #   Der Zuteilungsdivisor ist so zu bestimmen, dass insgesamt so viele
    #   Sitze auf die Landeslisten entfallen, wie Sitze zu vergeben sind.
    #   Dazu wird zunächst die Gesamtzahl der Zweitstimmen aller zu berücksichtigenden
    #   Landeslisten durch die Zahl der jeweils nach Absatz 1 Satz 3
    #   verbleibenden Sitze geteilt.

    print("Max num seats input", available_seats)
    preliminary_divisor = zweitstimmen_by_party.sum() / available_seats
    allocation_of_seats = sainte_lague_new(
        preliminary_divisor, zweitstimmen_by_party, available_seats
    )

    # Entfallen danach mehr Sitze auf die Landeslisten, als Sitze zu vergeben sind,
    #   ist der Zuteilungsdivisor so HERAUFZUSETZEN, dass sich bei der Berechnung
    #   die zu vergebende Sitzzahl ergibt; entfallen zu wenig Sitze auf die Landeslisten,
    #   ist der Zuteilungsdivisor entsprechend herunterzusetzen.
    return allocation_of_seats


def sainte_lague_last(preliminary_divisor, data, available_seats, direktmandate):
    """Iterative Sainte-Lague procedure which applies core_sainte_lague

    Input:
    preliminary_divisor (float): Guess for the divisor
    data (pd.DateFrame): data processed with divisors (e.g. votes by party)
    available_seats (int): number of seats to be allocated
    direktmandate (pd.DataFrame): number of Direktmandate by Bundesland

    Output:
    allocated_seats (pd.DataFrame): seats by party, state, etc.

    """

    # Jede Landesliste (jedes Bundesland) erhält so viele Sitze, wie sich nach Teilung der Summe
    # ihrer erhaltenen Zweitstimmen (der Bevölkerung) durch einen Zuteilungsdivisor ergeben.
    prel_allocated_seats = data.divide(preliminary_divisor).copy()

    # "Zahlenbruchteile unter 0,5 werden auf die darunter liegende ganze Zahl abgerundet,
    #  solche über 0,5 werden auf die darüber liegende ganze Zahl aufgerundet. "
    prel_allocated_seats = prel_allocated_seats.round(0).astype(int)
    allocated_seats = pd.concat([prel_allocated_seats, direktmandate]).max(level=0)

    # Calculate sum of listenplaetze after first iteration
    sum_of_seats = allocated_seats.sum()

    if sum_of_seats != available_seats:
        if sum_of_seats > available_seats:
            preliminary_divisor = preliminary_divisor + 50
        elif sum_of_seats < available_seats:
            preliminary_divisor = preliminary_divisor - 50
        allocated_seats = sainte_lague_last(
            preliminary_divisor,
            data,
            available_seats,
            direktmandate,
        )

    return allocated_seats


def last_allocation_seats(zweitstimmen_by_party, initial_seats_by_state, direktmandate):
    """Implementation of Bundeswahlgesetz
    § 6 Wahl nach Landeslisten (2021) Absatz 1 und 2,
    Heft 3. Endgültige Ergebnisse nach Wahlkreisen (2017) p. 398
    describes the procedure a bit different

    Input:
    zweitstimmen_by_party (pd.DataFrame): Zweitstimmen by party
    initial_seats_by_state (int): number of seats in parliament for the
        respective Bundesland (depends on population, is published)
    direktmandate (pd.DataFrame): number of Direktmandate by Bundesland


    Output:
    allocation_of_seats (pd.DataFrame):
    """

    # Use Sainte-Lague Zuteilungsdivisor to calculate seats by party
    #   Der Zuteilungsdivisor ist so zu bestimmen, dass insgesamt so viele
    #   Sitze auf die Landeslisten entfallen, wie Sitze zu vergeben sind.
    #   Dazu wird zunächst die Gesamtzahl der Zweitstimmen aller zu berücksichtigenden
    #   Landeslisten durch die Zahl der jeweils nach Absatz 1 Satz 3
    #   verbleibenden Sitze geteilt.

    print("Max num seats input", initial_seats_by_state)
    preliminary_divisor = zweitstimmen_by_party.sum() / initial_seats_by_state
    allocation_of_seats = sainte_lague_last(
        preliminary_divisor,
        zweitstimmen_by_party,
        initial_seats_by_state,
        direktmandate,
    )

    # Entfallen danach mehr Sitze auf die Landeslisten, als Sitze zu vergeben sind,
    #   ist der Zuteilungsdivisor so HERAUFZUSETZEN, dass sich bei der Berechnung
    #   die zu vergebende Sitzzahl ergibt; entfallen zu wenig Sitze auf die Landeslisten,
    #   ist der Zuteilungsdivisor entsprechend herunterzusetzen.
    return allocation_of_seats


def bundestagswahl_2013_2017(
    erststimmen,
    zweitstimmen_bundesland,
    zweitstimmen_bundesgebiet,
    bundesländer_wahlkreise,
    initial_seats_by_state,
):
    """calculaute results for bundestagswahl 2013 and 2017

    Input:
    # TODO

    Output:
    VARIOUS OUTPUTS


    """

    # * Calculate Direktmandate.
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

    eligible = eligible_parties(
        zweitstimmen_bundesgebiet, direktmandate_bundesland.sum(axis=1)
    )

    # Keep eligible parties
    zweitstimmen_bundesland = zweitstimmen_bundesland.loc[eligible]

    listenplätze_bundesland = pd.DataFrame(
        index=zweitstimmen_bundesland.index, columns=zweitstimmen_bundesland.columns
    )

    for bundesland in bundesländer_wahlkreise.keys():
        # Listenplätze
        print("Bundesland:", bundesland)
        listenplätze_bundesland[bundesland] = allocation_seats_after2013(
            zweitstimmen_bundesland[bundesland], initial_seats_by_state.loc[bundesland]
        )

    # * Calculate number of seats before Ausgleichsmandate
    mindestsitzzahl = pd.DataFrame(
        index=eligible, columns=bundesländer_wahlkreise.keys()
    )

    # temp = list(set(direktmandate_bundesland.index.tolist()) - set(eligible))
    # listenplätze_bundesland.loc[temp] = 0
    for bundesland in bundesländer_wahlkreise.keys():
        for partei in eligible:
            mindestsitzzahl.loc[partei, bundesland] = max(
                listenplätze_bundesland.loc[partei, bundesland],
                direktmandate_bundesland.loc[partei, bundesland],
            )
    mindestsitzzahl.index.rename("Partei", inplace=True)
    mindestsitzzahl["sum_sitze"] = mindestsitzzahl.sum(axis=1)

    # * Number of Ausgleichsmandate (definite size of Bundestag)
    zweitstimmen_bundesgebiet.columns = ["Zweitstimmen"]
    # Keep eligible parties
    zweitstimmen_bundesgebiet = zweitstimmen_bundesgebiet.loc[eligible]

    bundestag_seats_bef_ausgleichsmdte = zweitstimmen_bundesgebiet.join(mindestsitzzahl)
    bundestag_seats_bef_ausgleichsmdte["divisor"] = (
        bundestag_seats_bef_ausgleichsmdte["Zweitstimmen"]
        / bundestag_seats_bef_ausgleichsmdte["sum_sitze"]
    )
    min_divisor = bundestag_seats_bef_ausgleichsmdte["divisor"].min()
    bundestag_seats_bef_ausgleichsmdte["seats_unrounded"] = (
        bundestag_seats_bef_ausgleichsmdte["Zweitstimmen"] / min_divisor
    )
    bundestag_seats_bef_ausgleichsmdte[
        "seats_rounded"
    ] = bundestag_seats_bef_ausgleichsmdte["seats_unrounded"].round(0)

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
            bundestag_seats_bef_ausgleichsmdte.loc[partei, "seats_rounded"],
            direktmandate_bundesland_t[partei],
        )

    # * Determine number of Ausgleichs- und Überhangmandate by party and Bundesland

    ausgleich_and_überhang = pd.DataFrame(
        index=zweitstimmen_bundesland_t.index,
        columns=pd.MultiIndex.from_product(
            [
                zweitstimmen_bundesland_t.columns.tolist(),
                ["Sum", "Überhang", "Ausgleich"],
            ]
        ),
    )

    ausgleich_and_überhang.loc["Hamburg", ("CDU", "Sum")] = 1

    for bundesland in bundestagssitze_bundesland.index.tolist():
        for partei in zweitstimmen_bundesland_t.columns:
            ausgleich_and_überhang.loc[
                bundesland, (partei, "Sum")
            ] = bundestagssitze_bundesland.loc[bundesland, partei]
            ausgleich_and_überhang.loc[bundesland, (partei, "Ausgleich")] = (
                ausgleich_and_überhang.loc[bundesland, (partei, "Sum")]
                - bundestag_seats_bef_ausgleichsmdte.loc[partei, bundesland]
            )
            ausgleich_and_überhang.loc[bundesland, (partei, "Überhang")] = max(
                0,
                direktmandate_bundesland.loc[partei, bundesland]
                - listenplätze_bundesland.loc[partei, bundesland],
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
                sum_seats_coalition
                + bundestag_seats_bef_ausgleichsmdte.loc[partei, "seats_rounded"]
            )
        possible_coalition.loc[posble_coalitions, "sum_seats"] = sum_seats_coalition

    necc_votes_maj = math.ceil(
        bundestag_seats_bef_ausgleichsmdte["seats_rounded"].sum() / 2
    )
    possible_coalition["margin"] = possible_coalition["sum_seats"] - necc_votes_maj
    possible_coalition["possible coalition"] = possible_coalition["margin"].apply(
        lambda x: "possible" if x >= 0 else "not possible"
    )

    return bundestagssitze_bundesland, ausgleich_and_überhang, possible_coalition
