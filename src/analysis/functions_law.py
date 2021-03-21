"""Implementation of current law that translates votes into seats in parliament
Bundeswahlgesetz §6

https://www.gesetze-im-internet.de/bwahlg/__6.html
https://www.bundestagswahl-bw.de/sitzberechnung-btw#c31948

"""


def partition_of_votes(raw_data, wahlkreise):
    """ Partition the raw data into "Erststimmen" und "Zweitstimmen".

    Input:
    raw_data (DataFrame): cleaned election data
    wahlkreise (list): list with all Wahlkreise

    Output:
    erststimmen (DataFrame): By party the number of Erststimmen in each Wahlkreis
    zweitimmen (DataFrame): By party the number of Zweitstimmen in each Wahlkreis

    """

    column_names = ['Partei'] + wahlkreise
    erststimmen = raw_data[raw_data['Stimme'] == 'Erststimmen'].loc[:, column_names].copy()
    zweitstimmen = raw_data[raw_data['Stimme'] == 'Zweitstimmen'].loc[:, column_names].copy()

    return erststimmen, zweitstimmen


def direktmandate(votes_by_party):
    """ Determine party that wins Direktmandat

    Input:
    votes_by_party (DataFrame): By party the number of votes

    Output:
    direktmandat(DataFrame): Indicates that party that wins Direktmandat
    """

    direktmandat = votes_by_party == votes_by_party.max()
    direktmandat = direktmandat.astype(int)
    return direktmandat


def eligible_parties(data, direktmandate):
    """ Determine which parties reach the Bundestag in a federal state.

    Input:
    data (DataFrame): cleaned data
    direktmandate (DataFrame): By party the number of Direktmandate

    Output:
    eligible_parties (list): all parties that are eligible for BT seats
    """
    
    bundesgebiet = data[data['Stimme'] == 'Zweitstimmen'].loc[:, ['Partei', 'Bundesgebiet']].copy()
    bundesgebiet.set_index(['Partei'], inplace=True)
    bundesgebiet = bundesgebiet.div(bundesgebiet.sum(axis=0))
    bundesgebiet.reset_index(inplace=True)

    eligible_direktmandate = direktmandate[direktmandate > 3].index.tolist()
    eligible_huerde = bundesgebiet[bundesgebiet["Bundesgebiet"] > 0.05].loc[:, 'Partei'].tolist()

    eligible_parties = list(dict.fromkeys(eligible_direktmandate + eligible_huerde))

    return eligible_parties


def zweitstimmenanteil_by_state(data, bundesländer):
    """ Determine the number of Bundestag seats by party for each federal state.

    Input:
    data (DataFrame): cleaned data
    bundesländer (list): list of federal states

    Output:
    bt_seats_by_state (DataFrame): By party the number of BT seats in each Bundesland

    """
    
    column_names = ['Partei'] + bundesländer
    zweitstimmen_by_state = data[data['Stimme'] == 'Zweitstimmen'].loc[:, column_names].copy()
    zweitstimmen_by_state.set_index(['Partei'], inplace=True)
    zweitstimmen_by_state = zweitstimmen_by_state.div(zweitstimmen_by_state.sum(axis=0))

    return zweitstimmen_by_state


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
    listenplaetze = party_votes.divide(preliminary_divisor).copy()

    # "Zahlenbruchteile unter 0,5 werden auf die darunter liegende ganze Zahl abgerundet,
    #  solche über 0,5 werden auf die darüber liegende ganze Zahl aufgerundet. "
    listenplaetze = listenplaetze.round(0).astype(int)

    # Calculate sum of listenplaetze after first iteration
    sum_of_listenplaetze = listenplaetze.sum()

    if sum_of_listenplaetze > total_available_listenplaetze:
        sainte_lague(preliminary_divisor + 0.01, party_votes)
    else:
        return listenplaetze


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
