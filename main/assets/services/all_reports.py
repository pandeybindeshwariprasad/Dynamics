import json
# import time
from elasticsearch import Elasticsearch, helpers
# from elasticsearch_dsl import Search
import csv


# Elastic search
# es = Elasticsearch([{'host':'localhost','port':9200}], timeout=30) # local
# es.indices.put_settings(index='dynamic_pdfs', body={"index": {"max_result_window": 200000}})
# es = Elasticsearch(hosts="10.40.40.64:9200") # server
es = Elasticsearch([{'host':'10.40.40.64','port':9200}], timeout=60, max_retries=2, retry_on_timeout=True)
# el_index_name = 'dynamics'

def _build_query(keywords, sections=None, parent_bool='must'):
    """
    Create a Json for an Elasticsearch query using the given
    keywords and sections. If no sections are given then the query
    is across the whole document.

    This is compiled iteratively, using a structure of parent and
    children elements. The children elements are created within the
    parent elements; ie. the children queries are sub queries of the
    parent query. A child is created for each keyword.
    Args:
        keywords: the terms to be searched for
        sections: the pages to be searched in (optional)
        parent_bool: determines if this search requires all the
                     keywords to match (must means it does)

    Returns: the built query as a json object

    """
    print("inside _build_query...!")
    # parent query is the master query; it contains all of the querying
    # logic for the elastic query.
    parent_query = []

    # if sections was given, compile an extra query, to ensure that only
    # results within the given sections are returned
    print('sections: ', sections)
    # exit(0)
    if sections:
        section_statements = []
        for section in sections:
            section_statement = {
                "match_phrase": {
                    "section": {
                        "query": section,
                        "boost": 0
                    }
                }
            }
            section_statements.append(section_statement)

        section_query = {
            "bool": {
                "should": section_statements
            }
        }
    else:
        section_query = None

    weighting_dict = {
        "body": 1,
        "section": 0.5,
        "name": 0.05,
    }

    # create a query for each keyword. This creates a should query with
    # each alternative as one of the should components.

    # create lists and dictionaries for alternative boost

    exec_summary_list = ['executive summary', 'key messages', 'key findings', 'overview']
    exec_weighting_dict = {
        "body": 1,
        "section": 2,
        "name": 0.2
    }

    operations_list = ['operations']
    operations_weighting_dict = {
        "body": 1,
        "section": 3,
        "name": 0.2
    }

    separation_list = ['separation', 'carve-out', 'standalone', 'it', 'function']
    separation_weighting_dict = {
        "body": 1,
        "section": 2,
        "name": 0.1
    }

    hr_list = ['hr', 'people', 'staff', 'headcount', 'metrics', 'kpi', 'financial metrics']
    hr_weighting_dict = {
        "body": 1,
        "section": 1,
        "name": 0.1
    }

    # if query: hr/people/staff/headcount and match
    for keyword in keywords:
        child_query = []
        # for alt_keyword in keyword.alt_list(string=True):
        for alt_keyword in keywords:
            if alt_keyword in exec_summary_list:
                for field, boost in exec_weighting_dict.items():
                    child_statement = {
                        "match_phrase": {
                            field: {
                                "query": alt_keyword,
                                "boost": boost
                            }
                        }
                    }
                    # this adds the the search within the given field to
                    # the should-query
                    child_query.append(child_statement)
            elif alt_keyword in operations_list:
                for field, boost in operations_weighting_dict.items():
                    child_statement = {
                        "match_phrase": {
                            field: {
                                "query": alt_keyword,
                                "boost": boost
                            }
                        }
                    }
                    # this adds the the search within the given field to
                    # the should-query
                    child_query.append(child_statement)
            elif alt_keyword in separation_list:
                for field, boost in separation_weighting_dict.items():
                    child_statement = {
                        "match_phrase": {
                            field: {
                                "query": alt_keyword,
                                "boost": boost
                            }
                        }
                    }
                    # this adds the the search within the given field to
                    # the should-query
                    child_query.append(child_statement)
            elif alt_keyword in hr_list:
                for field, boost in hr_weighting_dict.items():
                    child_statement = {
                        "match_phrase": {
                            field: {
                                "query": alt_keyword,
                                "boost": boost
                            }
                        }
                    }
                    # this adds the the search within the given field to
                    # the should-query
                    child_query.append(child_statement)
            else:
                for field, boost in weighting_dict.items():
                    # this is the statement to search within the given
                    # field with the given boost
                    child_statement = {
                        "match_phrase": {
                            field: {
                                "query": alt_keyword,
                                "boost": boost
                            }
                        }
                    }
                    # this adds the the search within the given field to
                    # the should-query
                    child_query.append(child_statement)

        # this is the statement to search for a given keyword within
        # the fields
        parent_statement = {
            "bool": {
                "should": child_query
            }
        }

        # this adds the keyword specific should-query to the overall
        # must-query
        parent_query.append(parent_statement)

    # this converts the dictionary to a json object
    # if there are sections specified it queries for those pages
    if sections:
        query = {
            "bool": {
                parent_bool: parent_query,
            }
        }
        query['bool']['minimum_should_match'] = 1
        query['bool']['filter'] = section_query

    else:
        # otherwise it just searches all the pages
        query = {
            "bool": {
                parent_bool: parent_query,
            }
        }

    # highlight is used to return the evidence of each hit.
    highlight = {
        "highlight_query": {
            "bool": {
                parent_bool: parent_query,
            }
        },
        "order": "score",
        "fields": {
            "body": {
                "number_of_fragments": 20
            },
            "section": {
                "number_of_fragments": 0
            },
            "name": {
                "number_of_fragments": 0
            }
        }
    }

    query = json.dumps({
        "query": query,
        "highlight": highlight
    })

    return query


def _compile_results(results):
    """
    Extract the hits from the results of an elastic search. Then
    create a ResultPage for each page that returned at least one
    hit. Sort the result pages by score and return the best matching
    page and a sorted list of the other pages.

    Args:
        results: The results of an elasticsearch over this file.

    Returns:
        page_to_view: the highest scoring page.
        sorted_pages: a list of result pages, sorted by score

    """

    # sorts the results based on their relevancy score
    pages = results['hits']['hits']
    elastic_pages = []
    # a mapping dict is used so order can be maintained and objects
    # can be found according to page number
    for i, page in enumerate(pages):
        score = page['_score']
        page_number = page['_source']['page_number']
        text = page['_source']['body']
        evidence = page['highlight']
        file_name = page['_source']['file_name']

        result_page = (score, page_number, evidence, text, file_name)
        elastic_pages.append(result_page)

    if len(elastic_pages) == 0:
        return
    # print("elastic_pages: ", elastic_pages)
    # exit(0)
    sorted_pages = sorted(elastic_pages, key=lambda x: x[0],
                          reverse=True)

    page_to_view = sorted_pages[0]
    return page_to_view, sorted_pages


def search_index(keywords, index_name='', pages=None):
    print("Inside search_index.....")
    query = _build_query(keywords, pages)
    print('Search completed...!', index_name)
    # print("Executing the query for the search")
    # # executes the built search
    print(index_name, ': Filtering the data and converting into json!')

    flag = 1
    results_lst = []
    # res = es.search(index="myIndex", doc_type='myType', body=doc, scroll='1m')
    # scroll = res['_scroll_id']
    scroll_id = None
    number_of_hits = 0
    while flag == 1:
        print(flag)
        if scroll_id is None:
            results = es.search(index=index_name, body=query, size=10000, scroll='1m')
            scroll_id = results['_scroll_id']
            # print("results['hits']['total']: ", results['hits']['total'])
            number_of_hits = results['hits']['total'] # ['value']

        else:
            results = es.scroll(scroll_id=scroll_id, scroll='1m')
            print("results_lst len else: ", len(results_lst))
            print("number_of_hits len else: ", number_of_hits)

        comp_rst = _compile_results(results)
        if number_of_hits != 0:
            results_lst = results_lst + comp_rst[1]
        if len(results_lst) == number_of_hits:
            flag = 0

    print("There were {0} hits".format(number_of_hits))

    print("results_lst: ", len(results_lst))
    # exit(0)
    return [0, results_lst]


class ResultPage:
    """
    A handler for a single page that has been returned from an elastic
    search.

    Args:
        model_file: the File model of the file this belongs to
        _score: the relevancy score of the page
        page_number: the page number of the page this refers to
        text: the raw text of the page
        evidence: a dictionary of the evidence found per field

    """

    def __init__(self, _score, page_number, text, evidence):
        self.score = _score
        self.page_number = page_number
        self.text = text
        # self.model = ModelPage.objects.get(file=model_file,
        #                                    page_number=self.page_number)
        # if there were previous matches on this page, give a boost to the
        # score
        # if self.model.previous_match:
        #     num_past_matches = len(Result.objects.filter(file=model_file,
        #                                                  page=self.model))
        #     self.score += 3 * num_past_matches
        #
        self.evidence = evidence
        self.section_hits = bool('section' in evidence.keys())
        self.name_hits = bool('name' in evidence.keys())

    def __repr__(self):
        return "{0}: {1}".format(self.page_number, self.score)


if __name__ == '__main__':
    # start_1 = time.time()
    el_index_name = 'dynamics'
    word_lst = ['Cost', 'IT', 'Separation']
    # search_res = search_index(['cost', 'IT', 'separation'], index_name='dynamic_pdfs', pages=None)
    search_res = search_index(['cost', 'IT', 'separation'], index_name='dynamics', pages=None)
    print("Writing data into csv file")
    with open('test_count_words_07_2020.csv', 'w', encoding="utf8", newline='') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['Score', 'Page No.', 'Page Text', 'File Name'] + [w + " count" for w in word_lst] +
                         ["Keywords"] + [w + " file_count" for w in word_lst] )
        # cccc
        main_list = []
        file_count_dict = dict()
        for row in search_res[1]:
            page_txt_lst = row[3].replace("\n", '').lower().split()
            wordfreq = [page_txt_lst.count(w.lower()) for w in word_lst]
            count_lst = list(zip(word_lst, wordfreq))

            # csv_out.writerow((row[0], row[1], row[3].replace("\n", '').strip(), row[4]))
            row_col_lst = [row[0], row[1], row[3].replace("\n", '').strip(), row[4].split('\\')[-1]] # + count_lst
            word_appear = []
            for cw in count_lst:
                row_col_lst.append(str(cw[1]))
                if cw[1] != 0:
                    word_appear.append(cw[0])

            # add file count
            filename = row_col_lst[3]
            if filename not in file_count_dict.keys():
                file_count_dict[filename] = {count_lst[0][0]: count_lst[0][1],
                                             count_lst[1][0]: count_lst[1][1],
                                             count_lst[2][0]: count_lst[2][1],
                                             # count_lst[3][0]: count_lst[3][1],
                                             }
            else:
                file_count_dict[filename] = {count_lst[0][0]: count_lst[0][1] + file_count_dict[filename][count_lst[0][0]],
                                             count_lst[1][0]: count_lst[1][1] + file_count_dict[filename][count_lst[1][0]],
                                             count_lst[2][0]: count_lst[2][1] + file_count_dict[filename][count_lst[2][0]],
                                             # count_lst[3][0]: count_lst[3][1] + file_count_dict[filename][count_lst[3][0]],
                                             }
            # csv_out.writerow(row_col_lst)
            s = '|'.join(word_appear)
            row_col_lst.append(s)
            main_list.append(row_col_lst)
        # pprint(file_count_dict)
        # exit(0)
        for row_lst in main_list:
            file_name = row_lst[3]
            for fw in word_lst:
                row_lst.append(file_count_dict[file_name][fw])
            csv_out.writerow(row_lst)

    # end_1 = time.time()
    # print("Total time of run 1: ", end_1 - start_1)
    print("Process completed....!")
