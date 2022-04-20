from main import models as md

def queryToList(query):
    """

    Take query set containing list of searches (description) from StoredSearch and transform into list

    :param query:
    :return: list
    """
    new_list = []
    for my_dict in list(query.values("del_id", "description")):
        for key, value in my_dict.items():
            new_list.append(value)

    return new_list


def query_list(query):
    """

    Query StoredSearch to find ID and description - output descriptions in order of ID

    :param query:
    :return: list of dictionaries
    """
    # get id and description from db
    search_list = []
    for dict in list(md.StoredSearch.objects.all().values("del_id", "description")):
        if dict['del_id'] in queryToList(query):
            search_list.append(dict)

    # order on id
    search_list = sorted(search_list, key=lambda k: k["del_id"])

    # append dictionary containing description to list
    my_list = []
    check_for_description = list()
    for my_dict in search_list:
        for key, value in my_dict.items():
            if key == 'description' and value not in check_for_description:
                new_dict = {'description': value}
                my_list.append(new_dict)
                check_for_description.append(value)

    return my_list


def query_list_direct(query, searchset_id):
    """

    Take query set containing list of searches (description) from StoredSearch and transform into list

    :param query:
    :return: list of dictionary
    """
    # get id and description from db
    search_list = []
    for dict in list(md.StoredSearch.objects.filter(searchset_id=searchset_id).values("del_id", "description")):
        if dict['del_id'] in queryToList(query):
            search_list.append(dict)

    # order on id
    search_list = sorted(search_list, key=lambda k: k["del_id"])

    # append dictionary containing description to list
    my_list = []
    check_for_description = list()
    for my_dict in search_list:
        for key, value in my_dict.items():
            if key == 'description' and value not in check_for_description:
                new_dict = {'description': value}
                my_list.append(new_dict)
                check_for_description.append(value)

    return my_list


