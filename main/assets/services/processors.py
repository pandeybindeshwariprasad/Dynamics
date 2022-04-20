import os
import re
import subprocess
import logging
from Deloitte_Dynamics.settings import BASE_DIR, PRINT_STATEMENT
from time import sleep
from tika import parser

_dir = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(__name__)


# #### Processors ####
class PDFProcessor:
    """
    A processor to handle the conversion of a pdf into dictionaries for
    the index and pages of the file. The processor also handles
    extraction of peripheral information.

    The extraction of xml data is handled by methods using Apache Tika.

    Args:
        pdf: the path of the pdf file that is being converted
    """

    # start the tika server running to enable file reading
    server_path = os.path.join(
        BASE_DIR,
        "Deloitte_Dynamics\\static\\tika_files\\tika-server.jar"
    )
    server = subprocess.Popen(['java', '-jar', server_path], shell=True)

    def __init__(self, pdf):
        # Assigned in init
        self.pdf = pdf
        self.name = os.path.split(pdf)[-1].strip()
        self.contents_processor = ContentsProcessor(self)

        # Assigned Later
        self.number_of_pages = 0
        self.pages = {}
        self.page_names = {}
        self.meta_page = []
        self.project_name = None
        self.project_date = None
        self.page_contents = []
        self.poorly_extracted_paragraphs = 0
        self.contents = {}

    def process_pdf(self, server='http://localhost:9998'):
        """
        Run the methods to process the raw text into pages and sections
        and return the contents that were found.

        Returns: the contents of the pdf

        """

        raw_text, self.number_of_pages = self.read_pdf(server)
        logger.info("The file was read")
        paragraphs = self.split_paragraphs(raw_text)
        logger.info("Processing the paragraphs from this file")
        self.process_paragraphs(paragraphs=paragraphs)
        extraction_success = 100 - \
                             self.poorly_extracted_paragraphs / \
                             len(paragraphs) * 100
        logger.info("The paragraphs have been processed")
        logger.info(
            "Text extraction success rate {0}".format(extraction_success)
        )

        if PRINT_STATEMENT:
            print(self.contents_processor.contents)
        return self.contents_processor.contents

    def read_pdf(self, server):
        """
        Read the raw text from the pdf into xml format.

        Args:
            server: the url of the tika server being used to read the
                    file

        Returns: the xml text data of the pdf and the number of pages
                 in the pdf

        """

        counter = 0
        # if the file hasn't been processed yet (this is to wait in
        # case the tika server is still starting)
        file_read = False
        while not file_read:
            if counter == 10:
                # try ten times
                break
            else:
                if PRINT_STATEMENT:
                    print("attempt {0}".format(counter))
                counter = counter + 1
                try:
                    parsed = parser.from_file(self.pdf, server,
                                              xmlContent=True)
                    file_read = True
                except Exception as e:
                    print(e)
                    return
                if len(parsed) == 0:
                    sleep(1)
                else:
                    if PRINT_STATEMENT:
                        print("{0} has been read".format(self.name))
                    self.server.kill()
                    text = parsed['content'].strip()
                    raw_text = re.sub('&amp;', '&', text)
                    # count the number of pages in the text
                    number_of_pages = len(
                        re.findall(r'<div class="page">', raw_text))
                    return raw_text, number_of_pages
            counter += 1

    @staticmethod
    def split_paragraphs(raw_text):
        """
        Split the found text into paragraphs using the xml tags
        Returns: the split paragraphs

        """
        paragraphs = [paragraph.strip() for paragraph in
                      re.split(r"\s*</?[a-z]+ ?/?>+\s*", raw_text)]
        return paragraphs

    def process_paragraphs(self, paragraphs):
        """
        Process the paragraphs that were found into pages, try to find
        the project name and date from each paragraph and create a
        contents from the contents page in the document

        Returns: None
        """

        for paragraph in paragraphs:
            paragraph_processor = ParagraphProcessor(paragraph)
            # if this is an empty paragraph move on
            if len(paragraph_processor.text) == 0:
                continue

            # check if this is the end of a page
            page_marker = paragraph_processor.check_if_page_marker()

            # if this is not a new page and the paragraph was extracted
            # successfully
            if not page_marker and paragraph_processor.extraction_successful:
                if paragraph_processor.page_number == 0:
                    # if this is from page 0 it is meta data
                    self.meta_page.append(paragraph_processor.text)
                    continue

                # if this is the first line of a page
                elif paragraph_processor.page_number not in self.pages:
                    self.pages[paragraph_processor.page_number] = [
                        paragraph_processor.text, ]
                else:
                    self.pages[paragraph_processor.page_number].append(
                        paragraph_processor.text)

                # check if the paragraph contains the project name/date/footer
                project_name = paragraph_processor.search_for_project_name()
                project_date = paragraph_processor.search_for_project_date()

                # if these has not already been found and have been
                # found, assign them
                # short circuit this
                if project_name and not self.project_name:
                    self.project_name = project_name
                    logger.info("The project name was found to be {0}".format(
                        project_name))
                if project_date and not self.project_date:
                    self.project_date = project_date
                    logger.info("The project date was found to be {0}".format(
                        project_date))

                # check if the page name is on this page
                page_name = paragraph_processor.search_for_page_name()

                if page_name:
                    self.page_names[
                        paragraph_processor.page_number] = page_name

                # find any potential contents lines within this paragraph
                contents_lines = paragraph_processor.check_for_contents_lines()
                if contents_lines:
                    # add any potential contents lines to the page_contents
                    self.page_contents.extend(contents_lines)

            elif not paragraph_processor.extraction_successful:
                # if the paragraph was not extracted correctly,
                # add 1 to the count
                self.poorly_extracted_paragraphs += 1
                logger.debug(
                    "Line {0} on page {1} was logged as "
                    "poorly ""extracted".format(
                        paragraph_processor.page_number,
                        paragraph_processor.text
                    )
                )

            elif page_marker:
                if paragraph_processor.page_number not in self.pages:
                    self.pages[paragraph_processor.page_number] = []
                if paragraph_processor.page_number not in self.page_names:
                    self.page_names[paragraph_processor.page_number] = None
                # if this is the end of a page, use the contents
                # processor to update the contents based on the
                # potential contents lines that were found on this page
                self.contents_processor.validate_contents_lines(
                    self.page_contents, paragraph_processor.page_number - 1)
                self.contents_processor.update_contents(
                    paragraph_processor.page_number - 1)
                self.page_contents = []

        ParagraphProcessor.page_number = 0


class ParagraphProcessor:
    """
    Process a paragaph, extracting any useful information from
    each.

    This has methods to check for and extract project name,
    project date, page names, any contents/indexing information
    and identifies page tags.

    Args:
        paragraph: the paragraph to be processed
    """

    # a counter of which page is currently being processed
    page_number = 0

    def __init__(self, paragraph):

        # Initialisation
        self.text = paragraph.strip()  # the raw text of the paragraph

        if self.page_number == 0:
            self.extraction_successful = True
        else:
            self.extraction_successful = \
                len(re.findall(r"[#%/&*_\[\]\^\\\-=+()]", re.sub(r"\s", "",
                                                                 self.text))) < 15
            # this informs if the paragraph was extracted correctly

    def check_if_page_marker(self):
        """
        Check if this paragraph is in fact a page marker and adjusts the
        current page number accordingly

        Returns:
            True if marker, False if not

        """

        if self.text == '<div class="page">':
            ParagraphProcessor.page_number += 1
            return True
        return False

    def search_for_project_name(self):
        """
        Search this paragraph to see if it contains the name of the
        project.

        Returns:
            the found project name or false

        """

        try:
            project_name = re.search(r"(Project \w+)", self.text,
                                     re.IGNORECASE).group()
            # Search for the project name
            if project_name.endswith(str(self.page_number)):
                # Ensures the project name does not have the page number attached
                project_name = project_name.split(str(self.page_number))[0]
            return project_name
        except AttributeError:
            return None

    def search_for_project_date(self):
        """
        Search this paragraph to see if it contains the date of the
        project.

        Returns:
            the found project date or false

        """

        try:
            project_date = re.search(r"\d+[ ./\\][A-Za-z\d]+[ ./\\]\d{4}",
                                     self.text).group()
            return project_date
        except AttributeError:
            return None

    def search_for_page_name(self):
        """
        Search the paragraph for a page name

        Returns:
            The found page name or None

        """
        footer_search = re.search(r"[A-Z].+ [|] .*", self.text)
        if footer_search:
            footer = str(footer_search.group()).split("|")
            footer[1] = footer[1].split(str(self.page_number))[0]
            page_name = footer[-1].strip()
            return page_name

    def check_for_contents_lines(self):
        """
        Check if this paragraph has a line that is part of a contents
        page.
        Returns:
            a [list] of [tuples] of (section, start page) or False

        """

        contents_lines = re.findall(
            # r"^(?P<Section>(?!Page)[0-9A-Z a-z&,.()–-]+)[ +.]+ ?(?P<StartPage>\d+)$",
            r"^(?P<Section>[0-9A-Z a-z&,.()–-]+)[ +.]+ ?(?P<StartPage>\d+)$",
            # r"^(?P<Section>[\r\nA-Z a-z&,.()–-]+)([0-9\r\n]+Page )(?P<StartPage>\d+)$",
            self.text,
            re.MULTILINE)
        if contents_lines:
            contents_lines = [(contents_line[0].strip(), int(contents_line[1]))
                              for contents_line in contents_lines]

        return contents_lines


class ContentsProcessor:
    """
    This processor takes any suspected contents lines from a single
    page, checks that the page is indeed a contents page and then
    compiles a digital representation of the contents.

    Args:
         parent: the parent processor that this contents was generated
                 from.
    """

    def __init__(self, parent):
        self.parent_processor = parent

        self.contents = {}
        self.contents_declared = False
        self.previous_contents_page = None
        self.previous_sections_page = 0

        # a list of adjustments that need to be made from the pages
        # given by the contents page to the correct pages of the pdf
        self.page_adjustment = []
        # a mapping list to determine which page adjustment to use for
        # each page
        self.adjustment_boundaries = []
        self.validated = []

    def validate_contents_lines(self, page_contents, page_number):
        """
        Validate the given page contents using a series of logical
        checks to ensure no false positives are added

        Args:
            page_contents: the page contents to be validated
            page_number: the page these contents came from

        Returns:
            None
        """
        if self.contents:
            self.previous_sections_page = max(self.contents.values())

        validated_contents_lines = []
        i = 0
        for contents_line in page_contents:

            # the section name from this line
            section = re.sub(r'\.{2,}', '', contents_line[0])
            # the starting page of this section
            page_from_contents = contents_line[1]

            # if the line has the project name in, it is a page
            # declaration, ignore it
            if not self.parent_processor.project_name:
                self.parent_processor.project_name = self.parent_processor.name
            if re.search(self.parent_processor.project_name, section):
                logger.debug(
                    "the suggested contents line {0} on page {1} had the "
                    "project name in".format(str(section), page_number)
                )

            # if this line has a page number lower than the last
            # sections page, ignore it
            elif int(page_from_contents) < self.previous_sections_page:
                logger.debug(
                    "The suggested contents line {0} on page {1} had a page "
                    "number lower than the last sections page".format(str(section), page_number)
                )

            # if this line has a page number larger than the number of
            # pages, ignore it
            elif self.parent_processor.number_of_pages < int(page_from_contents):
                logger.debug(
                    "The suggested contents line {0} on page {1} had a page "
                    "number larger than the total number of pages".format(str(section), page_number)
                )

            # if this line has a name that is already in the contents,
            # ignore it
            elif str(section).strip() in self.contents.keys():
                logger.debug(
                    "The suggested contents line {0} on page {1} had a "
                    "section name that was already in in the contents".format(str(section), page_number)
                )

            else:
                # if this contents refers to the location of the
                # contents page
                if section == 'Contents':
                    self.contents_declared = True  # note that the page
                    # number of the contents has been referenced
                    page_adjustment = int(page_number) - int(
                        page_from_contents)
                    # if no page adjustments have been added yet
                    # (this is the first contents page)
                    if len(self.page_adjustment) == 0:
                        self.adjustment_boundaries.append(page_number)
                    self.page_adjustment = [page_adjustment, ]
                    self.previous_contents_page = page_number

                # if this is the first contents page and does not
                # reference the location of the contents page
                elif not self.previous_contents_page:
                    self.page_adjustment.append(page_number)
                    self.adjustment_boundaries.append(page_number)
                    self.previous_contents_page = page_number

                # if this is an extension of the previous contents page
                elif page_number == self.previous_contents_page + 1:
                    if not self.contents_declared:
                        self.page_adjustment[-1] += 1
                    self.adjustment_boundaries[-1] += 1
                    self.previous_contents_page = page_number

                # if this is a secondary contents page
                elif page_number > self.previous_contents_page + 1:
                    if page_from_contents < self.previous_sections_page:
                        self.page_adjustment.append(page_number)
                        self.adjustment_boundaries.append(page_number)
                    self.previous_contents_page = page_number
                # collect all the validated contents lines
                validated_contents_lines.append(
                    (
                        section,
                        int(page_from_contents),
                    )
                )
                # update the last section page declared
                self.previous_sections_page = int(
                    page_from_contents)

            i += 1

        # add the validated contents lines to the validated list
        self.validated.extend(validated_contents_lines)

    def update_contents(self, page_number):
        """
        Checks the found contents fit into the existing contents,
        adjusts the page number relative to its location
        and then adds to the contents

        Returns:

        """

        # if there are only a small amount of lines, its probably a
        # false positive
        if len(self.validated) < 5:
            for contents_line in self.validated:
                logger.debug(
                    "The suggested contents line {0} on page {1} found to be "
                    "on a page with not enough contents lines".format(
                        str(contents_line), page_number
                    )
                )
        else:
            # for each contents line that has been validated, find the
            # page adjustment that applies to it and adjust
            # its starting page by the appropriate amount, then
            # add it to the overall contents
            for contents_line in self.validated:
                page_adjustment = self.page_adjustment[-1]
                for i in range(len(self.adjustment_boundaries)):
                    if page_number <= self.adjustment_boundaries[i]:
                        page_adjustment = self.page_adjustment[i]

                section = contents_line[0]
                starting_page = contents_line[1] + page_adjustment

                self.contents[section] = starting_page
                self.previous_sections_page = starting_page
                logger.info(
                    "The suggested contents line {0} on page {1} was "
                    "accepted as a contents line".format(str(section),
                                                         page_number)
                )

            self.previous_contents_page = page_number
        self.validated = []
