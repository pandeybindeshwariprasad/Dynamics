import os
import re
import pandas as pd
import time
import json
import logging
from django.db import transaction
from Deloitte_Dynamics.settings import Y_DRIVE_LOGS, PRINT_STATEMENT
from .processors import PDFProcessor
from ...models import File as ModelFile, Section as ModelSection, \
    Page as ModelPage, \
    SearchSet, StoredSearch, Result, Keyword
from elasticsearch import Elasticsearch, helpers

es = Elasticsearch(hosts="10.40.40.64:9200", timeout=30, max_retries=2, retry_on_timeout=True) # Server
#es = Elasticsearch(hosts="127.0.0.1:9200")  # Local
logger = logging.getLogger(__name__)


class FileManager:
    """
        PDF file manager that handles the lifetime of the file from
        load to querying, has methods to parse the text
        from a PDF, sort and index the pages found in the PDF, store
        those pages in the Database/Elasticsearch and query the
        Elasticsearch index.
    """

    def __init__(self, path):
        self.name = os.path.split(path)[-1].strip().strip("'").strip('"')
        self.index_name = re.sub(r"[/.*<|>?', -]+", "_", self.name).lower()
        self.folder = path.split(self.name)[0]
        self.path = path
        self.index_name = re.sub(r"[/.*<|>?', -]+", "_", self.name).lower()
        self.processor = PDFProcessor(self.path)

        # Create a Django model for the file
        self.model_file, self.new = ModelFile.create(name=self.name)

        # Assigned Later
        self.index = {}
        self.pages = {}
        # the indexed pages of the document
        self.contents = {}

    def process_file(self):
        """
        Run the private methods that completely process the given file.
        These entail processing the pdf into pages, paragraphs and sections
        and then indexing each page to it's section using the digital contents
        Returns:
            None

        """

        logger.info("Started processing the file {0}".format(self.path))
        self.index = self.processor.process_pdf()
        # take the contents that were found during processing as a property
        self.index = self.processor.contents_processor.contents
        # collect the pages from the processor
        self.pages = self.processor.pages
        logger.info("Indexing the document")
        self._index_pages()

    def write_to_file(self):
        """
        Write the parsed text of the file to a log file. This is used
        for checking purposes mostly.

        The text is written by paragraph, by page and is seperated on a
        page by page basis using _____PAGE X______ syntax.
        Returns:
            None
        """

        extracted_folder_path = os.path.join(Y_DRIVE_LOGS, "01 EXTRACTED TEXT")
        extraction_path = os.path.join(extracted_folder_path,
                                       "{0}.txt".format(
                                           self.processor.project_name)
                                       )
        with open(extraction_path, "w+", errors="ignore") as fh:
            fh.write("File name: " + self.name + "\n\n\n")
            for page, paragraphs in self.pages.items():
                fh.write("\n\n____PAGE {0}____\n\n".format(page))
                for paragraph in paragraphs:
                    fh.write(str(paragraph) + "\n")

    def _index_pages(self):
        """
        Place each page into it's section, using the page numbers and
        the starting page from the contents. This is the method used to
        compile the contents.

        Returns: None

        """

        logger.info("Indexing pages")
        # if there was no contents page found
        if len(self.index) == 0 or 'Page' in self.index:
            # assign every page to a section called No Section.
            self.contents["No Section"] = {}
            for page_number, page_text in self.pages.items():
                self.contents["No Section"][page_number] = page_text
        else:
            # This is a trigger for the final section in the doc
            last_section = False
            # Create an iterator of the sections that were found, in order of
            # the starting page of each section.
            sorted_sections = iter(sorted(self.index, key=self.index.get))
            current_section = None
            next_section = next(sorted_sections)
            for page_number, page_text in self.pages.items():
                # if this page has a page number greater/equal than the
                # starting page of the next section, then move up one
                # section in the iterator.
                if page_number >= self.index[next_section] and \
                        not last_section:
                    current_section = next_section
                    # try and assign the next section, if it fails, this is
                    # the final section in the document.
                    try:
                        next_section = next(sorted_sections)
                    except StopIteration:
                        last_section = True

                if current_section not in self.contents:
                    self.contents[current_section] = {}
                self.contents[current_section][page_number] = page_text

        if PRINT_STATEMENT:
            print('INDEXED PAGES')
            print(self.contents)

    def store_pages(self):
        """
        Store the pages in the database and index. The database contains
        structural details, the index contains the text.

        Generate the File, Section, Page Models for this file. These are
        used to describe the structure of the document. Peripheral
        details such as project name are added to the models here.

        Also creates the Elasticsearch structure for this file. The file
        is used as an Elasticsearch index and each page is a document in
        that index.
        The Bulk API is then used to ingest this into the instance.
        Returns:
            None

        """

        logger.info("Storing the pages")
        # assign the peripheral information to the File model
        self.model_file.num_pages = self.processor.number_of_pages
        self.model_file.project_name = self.processor.project_name
        self.model_file.date = self.processor.project_date
        self.model_file.save()

        # loop through each section in the contents dictionary. For each
        # section (if the section exists) create a Section model, for each
        # page in the section, create a Page Model and a Document in
        # Elasticsearch.
        elastic_actions = []
        for section, section_pages in self.contents.items():
            # if not section:
            #     continue
            if not section:
                no_section_content = self.contents[section]
                del self.contents[section]
                section = "No section"
                self.contents[section] = no_section_content

            page_section = section
            first_page = min(section_pages.keys())
            last_page = max(section_pages.keys())
            # Django model creation for the section
            model_section, created = ModelSection.create(self.model_file,
                                                         section, first_page,
                                                         last_page)
            model_section.save()
            for page_number, page_text in section_pages.items():
                page_name = self.processor.page_names[page_number]
                # Django model creation for the page
                model_page, created = ModelPage.create(self.model_file,
                                                       page_number)
                model_page.section = model_section
                model_page.page_name = page_name
                model_page.save()

                # join the paragraphs with two blank lines between each
                page_text_joined = "\n\n\n".join(page_text)
                # create a document action with the given properties
                elastic_action = self._create_page_json(page_section,
                                                        page_number,
                                                        page_name,
                                                        page_text_joined)
                elastic_actions.append(elastic_action)
        helpers.bulk(es, elastic_actions)
        # the elasticsearch transaction can take up to 1 second, so wait
        # until it is complete
        time.sleep(5)
        if not PRINT_STATEMENT:
            print('MODEL SECTION Test')
            #print(model_section)

    def _create_page_json(self, page_section, page_number, page_name,
                          page_text):
        """
        Create a json object representing the given page. It can later be
        used to create an Elasticsearch document.
        Args:
            page_section: the section of the page
            page_number: the page number of the page
            page_name: the name of the page
            page_text: the text of the page

        Returns: The compiled json as a python dictionary.

        """

        elastic_action = {
            "_index": self.index_name,
            "_type": "page",
            "_id": self.index_name + str(page_number),
            "_source": {
                "timestamp": time.time(),
                "page_number": page_number,
                "section": page_section,
                "name": page_name,
                "body": page_text
            }
        }
        return elastic_action

    @staticmethod
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

        # parent query is the master query; it contains all of the querying
        # logic for the elastic query.
        parent_query = []

        # if sections was given, compile an extra query, to ensure that only
        # results within the given sections are returned
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
            for alt_keyword in keyword.alt_list(string=True):
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

    def _compile_results(self, results):
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
            result_page = ResultPage(self.model_file, score,
                                     page_number, text,
                                     evidence)
            elastic_pages.append(result_page)

        if len(elastic_pages) == 0:
            return

        sorted_pages = sorted(elastic_pages, key=lambda x: x.score,
                              reverse=True)

        page_to_view = sorted_pages[0]
        return page_to_view, sorted_pages

    def search_index(self, keywords, pages=None):
        """
        Compile an elastic query using _build_query. Then execute that
        query against the index corresponding to this file. If no hits are
        found, execute again but as a should query.

        Sort the results of the search using _compile_results
        Args:
            keywords: the terms to be searched for
            pages: the pages to be searched in (optional)

        Returns: the results of the search

        """

        logger = logging.getLogger(__name__)
        logger.info(
            "Building the query for the search with keywords {0}".format(
                keywords
            )
        )
        query = self._build_query(keywords, pages)

        logger.info("Executing the query for the search")
        # executes the built search
        results = es.search(
            index=self.index_name,
            body=query	
        )

        # if no hits were returned for all the keywords,
        # find the best matching page
        number_of_hits = results['hits']['total']
        logging.info("There were {0} hits".format(number_of_hits))
        if number_of_hits == 0:
            logging.warning("There were no hits for the search, trying with "
                            "should query")
            query = self._build_query(keywords=keywords, sections=pages,
                                      parent_bool="should")
            results = es.search(
                index=self.index_name,
                body=query
            )
        return self._compile_results(results)


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

    def __init__(self, model_file, _score, page_number, text, evidence):
        self.score = _score
        self.page_number = page_number
        self.text = text
        self.model = ModelPage.objects.get(file=model_file,
                                           page_number=self.page_number)
        # if there were previous matches on this page, give a boost to the
        # score
        if self.model.previous_match:
            num_past_matches = len(Result.objects.filter(file=model_file,
                                                         page=self.model))
            self.score += 3 * num_past_matches
        self.evidence = evidence
        self.section_hits = bool('section' in evidence.keys())
        self.name_hits = bool('name' in evidence.keys())

    def __repr__(self):
        return "{0}: {1}".format(self.page_number, self.score)


class SectionManager:
    """
    A manager to handle sections as independent objects.

    There is one method for this class, that returns the names of each
    section that were given to the manager. However this class exists to
    enable more to be done to sections if necessary later on.

    Args:
        sections: a string of section names split by commas.

    """

    def __init__(self, sections):
        if len(sections) == 0:
            self.sections = None
        else:
            self.sections = [int(section) for section in sections.split(",")]
            self.model_sections = [ModelSection.objects.get(id=section) for
                                   section in self.sections]

    def get_section_names(self):
        if self.sections:
            return [model_section.name.lower() for model_section in
                    self.model_sections]


class StoredSearchManager:
    """
    A manager to handle a single stored searche. It has methods to
    create a model for the stored search and create a placeholder result
    model for the stored search as well.

    Args:
        search_type: The type of search (FTE, P&L etc..)
        search_function: The function the search is on (Finance, HR etc..)
        keywords: The keywords that this search uses
        description: the human readable description of this search

    """

    def __init__(self, search_type, search_function, keywords,
                 description, del_id, unit_group, unit_group_default,
                 timestamp_group, timestamp_group_default, searchset_id):
        keywords = [keyword.strip() for keyword in keywords.split(",")]
        self.search_type = search_type
        self.search_function = search_function
        self.keywords = keywords
        self.description = description
        self.del_id = del_id
        self.unit_group = unit_group
        self.unit_group_default = unit_group_default
        self.timestamp_group = timestamp_group
        self.timestamp_group_default = timestamp_group_default
        self.model = None
        self.searchset_id = searchset_id

    def create_model(self):
        """Create a model of this search in the database"""

        model = StoredSearch.create(keywords=self.keywords,
                                    description=self.description,
                                    search_type=self.search_type,
                                    sub_type=self.search_function,
                                    del_id=self.del_id, searchset_id=self.searchset_id)
        model.save()
        return model


    def create_result(self, model_file):
        """create the result model for this search"""
        # result = Result.create(model_file, self.model, self.unit_group,
        #                        self.unit_group_default, self.timestamp_group,
        #                        self.timestamp_group_default)
        # result.save()
        result_model = Result.objects.filter(file_id=model_file, del_id=self.del_id)
        if len(result_model) > 0:
            # Update existing row
            result_model[0].search = self.model
            result_model[0].save()
            return result_model[0]
        else:
            # Create new row
            result = Result.create(model_file, self.model, self.unit_group,
                                   self.unit_group_default, self.timestamp_group,
                                   self.timestamp_group_default)
            result.save()
            return result

    def __str__(self):
        return str(self.description)


def generate_searches(search_file, model_file):
    """
    Convert an uploaded search file resource and loop through each
    row in the file, creating a stored search model for each row.
    """

    df = pd.read_excel(
        search_file,
        encoding='utf-8',
        error_bad_lines=False,
    )

    df = df.dropna(how="all", axis=1)

    with transaction.atomic():
        search_set, created = SearchSet.create(file_of_origin=search_file)
        logger.info("creating searches from {}".format(search_set.file_of_origin))
        # loop through the rows and generate searches
        for index, row in df.iterrows():
            # collect the variables detailed in the search file and create a
            # model using those variables.
            search_type = row.iloc[0]
            sub_type = row.iloc[1]
            keywords = row.iloc[3]
            description = row.iloc[4]
            unit_group = row.iloc[5]
            unit_group_default = row.iloc[6]
            timestamp_group = row.iloc[7]
            timestamp_group_default = row.iloc[8]
            del_id = row.iloc[9]
            searchset_id = search_set.id

            # create a stored search object to represent this row
            search = StoredSearchManager(search_type, sub_type,
                                         keywords, description, del_id,
                                         unit_group, unit_group_default,
                                         timestamp_group,
                                         timestamp_group_default, search_set.id)

            # Check for del_id
            if del_id is not None:
                storedsearch_model = StoredSearch.objects.filter(del_id=del_id,
                                                                 searchset_id=searchset_id)

                storedsearch_kwd_md = None
                if len(storedsearch_model) == 0:
                    search.model = search.create_model()
                else:
                    # Get keyword from storedsearch_keyword table for check duplicate
                    storedsearch_kwd_md = storedsearch_model[0].keywords.all()
                    # print("storedsearch_kwd_md---------------: ", storedsearch_kwd_md)
                    if storedsearch_model[0].description != description:
                        storedsearch_model[0].description = description
                        storedsearch_model[0].save()
                        # check for keyword for add in storedsearch
                        for kwd in keywords.split(","):
                            chk_kwd = Keyword.objects.filter(keyword=kwd)
                            if len(chk_kwd) > 0:
                                # keyword already exist
                                storedsearch_model[0].keywords.add(chk_kwd[0])
                            else:
                                # create new keyword
                                keyword = Keyword.create(kwd.strip())
                                storedsearch_model[0].keywords.add(keyword)
                        storedsearch_model[0].save()
                        search.model = storedsearch_model[0]
                    else:
                        # check for keyword for add in storedsearch
                        for kwd in keywords.split(","):
                            chk_kwd =  Keyword.objects.filter(keyword=kwd)
                            if len(chk_kwd)> 0:
                                # keyword already exist
                                storedsearch_model[0].keywords.add(chk_kwd[0])
                            else:
                                keyword, created = Keyword.create(kwd.strip())
                                storedsearch_model[0].keywords.add(keyword)

                        storedsearch_model[0].save()
                        search.model = storedsearch_model[0]
                # --------------- start ---------------------- #
                if storedsearch_kwd_md:
                    key_words_list = [str(k).lower().strip() for k in keywords.split(',')]  # new
                    for key_word_md in storedsearch_kwd_md:
                        if str(key_word_md) not in key_words_list:
                            search.model.keywords.remove(key_word_md)
                # ----------------- end ------------------------- #

            else:
                storedsearch_model = StoredSearch.objects.filter(description=description, searchset_id=searchset_id)

                if len(storedsearch_model) == 0:
                    search.model = search.create_model()
                else:
                    search.model = storedsearch_model[0]
            # search.model = search.create_model()
            # create the corresponding result for this search for this file
            result = search.create_result(model_file)
            # add this search to the overarching search set
            search_set.searches.add(search.model.pk)
            search_set.save()
            # # insert del_id, searchset_id and storedsearch_id in result model
            result.searchset_id = search_set.id
            result.del_id = del_id
            result.storedsearch_id = search.model.id
            result.save()

        return search_set
