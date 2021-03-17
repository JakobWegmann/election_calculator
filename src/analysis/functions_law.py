"""Implementation of current law that translates votes into seats in parliament
Bundeswahlgesetz §6

https://www.gesetze-im-internet.de/bwahlg/__6.html

"""
# import numpy as np
# import pandas as pd


def election_of_landeslisten_2021(
    zweitstimmen, total_available_listenplaetze, parties_eligible, direktmandate
):
    """Implementation of Bundeswahlgesetz
    § 6 Wahl nach Landeslisten (2021)

    Input:
    zweitstimmen(DataFrame): Zweitstimmen within a Bundesland
    parties_eligible(DateFrame): Parties that reached 5% or obtained
        3 Direktmandate (Bundesebene)
    total_available_listenplaetze(int): number of seats in parliament for the
        respective Bundesland (depends on population, is published)
    direktmandate(DataFrame): Direktmandate by party

    Output:
    parliamentarians_before_ausgleichsmandate(DataFrame):
    """
    # Für die Verteilung der nach Landeslisten zu besetzenden Sitze werden die für
    #   jede Landesliste abgegebenen Zweitstimmen zusammengezählt.
    #   zweitstimmen["sum_party"] = Depend on data strucute

    # Drop parties that are not eligible for Listenplätze
    #   (neither reach 5%  not won 3 Direktmandate)
    #

    # Use Sainte-Lague Zuteilungsdivisor to calculate seats by party
    #   Der Zuteilungsdivisor ist so zu bestimmen, dass insgesamt so viele
    #   Sitze auf die Landeslisten entfallen, wie Sitze zu vergeben sind.
    #   Dazu wird zunächst die Gesamtzahl der Zweitstimmen aller zu berücksichtigenden
    #   Landeslisten durch die Zahl der jeweils nach Absatz 1 Satz 3
    #   verbleibenden Sitze geteilt.

    divisor_step_1 = zweitstimmen["sum_party"].sum() / total_available_listenplaetze

    parliamentarians_before_ausgleichsmandate = sainte_lague(
        divisor_step_1, zweitstimmen, total_available_listenplaetze
    )

    # Entfallen danach mehr Sitze auf die Landeslisten, als Sitze zu vergeben sind,
    #   ist der Zuteilungsdivisor so HERAUFZUSETZEN, dass sich bei der Berechnung
    #   die zu vergebende Sitzzahl ergibt; entfallen zu wenig Sitze auf die Landeslisten,
    #   ist der Zuteilungsdivisor entsprechend herunterzusetzen.

    return parliamentarians_before_ausgleichsmandate


def sainte_lague(preliminary_divisor, party_votes, total_available_listenplaetze):
    """Iterative Sainte-Lague procedure

    Input:
    preliminary_divisor(float): Guess for the divisor
    party_votes(DateFrame): votes by party
    total_available_listenplaetze(int): number of seats in parliament for the
        respective Bundesland (depends on population, is published)

    Output:
    listenplaetze_by_party(DataFrame): seats by party
    """

    # Jede Landesliste erhält so viele Sitze, wie sich nach Teilung der Summe
    # ihrer erhaltenen Zweitstimmen durch einen Zuteilungsdivisor ergeben.
    party_votes["seats_before_round_1"] = (
        party_votes["zweitstimmmen"] / preliminary_divisor
    )

    # "Zahlenbruchteile unter 0,5 werden auf die darunter liegende ganze Zahl abgerundet,
    #  solche über 0,5 werden auf die darüber liegende ganze Zahl aufgerundet. "
    party_votes["seats_after_round_1"] = party_votes["seats_before_round_1"].round(0)

    # Calculate sum of seats after first iteration
    sum_of_seats = party_votes["seats_after_round_1"].sum()

    if sum_of_seats > total_available_listenplaetze:
        sainte_lague(preliminary_divisor + 0.01, party_votes)
    else:
        return party_votes["seats_after_round_1"]
