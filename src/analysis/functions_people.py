""" Implementation of allocation of seats for each Landesliste. 
"""

def prepare_lists(listen_by_party_and_bundesland):
    """ This function quickly prepares the dictionary by including
    in each dataframe a column Sitz_Bundestag.

    Input:
    listen_by_party_and_bundesland (dict): contains for each Bundesland
        a dictionary containing parties with their lists
    
    Output:
    listen_by_party_and_bundesland (dict): same as input only that
        a column Sitz_Bundestag is added
    """

    for bundesland in listen_by_party_and_bundesland.keys():
        for partei in listen_by_party_and_bundesland[bundesland].keys():
            listen_by_party_and_bundesland[bundesland][partei]["Sitz_Bundestag"] = 0
    
    return listen_by_party_and_bundesland


def mark_direktmandate(listen_by_party_and_bundesland, bundesländer_wahlkreise, direktmandate):
    """ This function marks the people who have won a Direktmandat by 
    putting a 1 into the column Sitz_Bundestag.

    Input:
    listen_by_party_and_bundesland (dict): contains for each Bundesland
        a dictionary containing parties with their lists and a column
        Sitz_Bundestag
    bundesländer_wahlkreise (dict): contains the for each Bundesland a list
        with all of the Wahlkreise in this Bundesland
    direktmandate (pd.DataFrame): indicates which party one in each Wahlkreis

    Output:
    listen_by_party_and_bundesland (dict): same as input only that
        column Sitz_Bundestag is modified for the Direktmandate

    """

    for bundesland in bundesländer_wahlkreise.keys():
        parteilisten = listen_by_party_and_bundesland[bundesland].copy()
        for wahlkreis in bundesländer_wahlkreise[bundesland]:
            won_by_party = direktmandate[direktmandate[wahlkreis] == 1].index[0]
            parteilisten[won_by_party].loc[parteilisten[won_by_party]["Wahlkreis_Bez"] == wahlkreis, "Sitz_Bundestag"] = 1
        listen_by_party_and_bundesland[bundesland] = parteilisten

    return listen_by_party_and_bundesland


def keep_eligible_parties(listen_by_party_and_bundesland, eligible_parties):
    """ This function shrinks the dictionary listen_by_party_and_bundesland
    to the eligible parties.

    Input:
    listen_by_party_and_bundesland (dict): contains for each Bundesland
        a dictionary containing all parties
    eligible_parties (dict): list with parties that are eligible for
        the Bundestag

    Output:
    listen_by_party_and_bundesland (dict): same as input only that
        all non-eligible parties are thrown out

    """

    for bundesland in listen_by_party_and_bundesland.keys():
        parteilisten = listen_by_party_and_bundesland[bundesland].copy()
        for partei in listen_by_party_and_bundesland[bundesland].keys():
            if partei not in eligible_parties:
                parteilisten.pop(partei)
            else:
                pass
        listen_by_party_and_bundesland[bundesland] = parteilisten

    return listen_by_party_and_bundesland
  

def allocate_listenplaetze(
listen_by_party_and_bundesland, 
bundesländer,
eligible_parties,
available_list_seats,
):
    """ This function shrinks the dictionary listen_by_party_and_bundesland
    to the eligible parties.

    Input:
    listen_by_party_and_bundesland (dict): contains for each Bundesland
        a dictionary containing the eligible parties with their lists 
        and a column Sitz_Bundestag which is already marked for Direktmandate
    bundesländer (list): contains all Bundesländer
    eligible_parties (list): all parties eligible for the Bundestag
    available_list_seats (pd.DataFrame): contains for each Bundesland (column)
        the number of available list seats for each party (row)

    Output:
    listen_by_party_and_bundesland (dict): same as input but now with Sitz_Bundestag
        marked also for the list candidates 

    """

    for bundesland in bundesländer:
        parteilisten = listen_by_party_and_bundesland[bundesland].copy()
        for partei in eligible_parties:
            if available_list_seats.loc[partei, bundesland] > 0:
                to_replace = parteilisten[partei].loc[parteilisten[partei]["Sitz_Bundestag"] == 0].copy()
                to_replace["Sitz_Bundestag"].iloc[:(available_list_seats.loc[partei, bundesland])] = 1
                parteilisten[partei].loc[parteilisten[partei]["Sitz_Bundestag"] == 0] = to_replace
            else:
                pass
        listen_by_party_and_bundesland[bundesland] = parteilisten

    return listen_by_party_and_bundesland


def tag_bundestagsabgeordnete(
listen_by_party_and_bundesland,
bundesländer_wahlkreise,
direktmandate,
eligible_parties,
bundesländer,
available_list_seats,
):
    """ This function tags all people who have eventually become
    a member of the Bundestag.

    Input:
    listen_by_party_and_bundesland (dict): contains for each Bundesland
        a dictionary containing the eligible parties with their lists 
        and a column Sitz_Bundestag which is already marked for Direktmandate
    bundesländer_wahlkreise (dict): contains the for each Bundesland a list
        with all of the Wahlkreise in this Bundesland
    direktmandate (pd.DataFrame): indicates which party one in each Wahlkreis
    bundesländer (list): contains all Bundesländer
    eligible_parties (list): all parties eligible for the Bundestag
    available_list_seats (pd.DataFrame): contains for each Bundesland (column)
        the number of available list seats for each party (row)

    Output:
    listen_by_party_and_bundesland (dict): same as input but now with Sitz_Bundestag
        marked also for the list candidates 

    """

    listen_by_party_and_bundesland = keep_eligible_parties(
        listen_by_party_and_bundesland, 
        eligible_parties,
    )

    listen_by_party_and_bundesland = prepare_lists(listen_by_party_and_bundesland)

    listen_by_party_and_bundesland = mark_direktmandate(
        listen_by_party_and_bundesland,
        bundesländer_wahlkreise,
        direktmandate,
    )

    listen_by_party_and_bundesland = allocate_listenplaetze(
        listen_by_party_and_bundesland,
        bundesländer,
        eligible_parties,
        available_list_seats,
    )

    return listen_by_party_and_bundesland
  