import os
import unittest
from ...services import processors

server = 'http://localhost:9998'
test_dir = os.getcwd()


class PDFProcessorTest(unittest.TestCase):
    """
    1. PDF Processing
    """

    def test_read__valid_pdf(self):
        """
        (a) Verify that read_pdf returns a string and an int
        """

        processor = processors.PDFProcessor(os.path.join(test_dir, 'SAMPLE.pdf'))
        text, number_of_pages = processor.read_pdf(server)

        # ASSERTIONS
        # (a)
        self.assertEqual((str, int), (type(text), type(number_of_pages)))

    def test_split_paragraphs(self):
        """
        (b) Verify that split_paragraphs creates a list of paragraphs
        """

        processor = processors.PDFProcessor(r"")
        raw_text = """
                <html xmlns="http://www.w3.org/1999/xhtml">
                <head>
                <meta name="date" content="2017-11-01T15:39:01Z" />
                <meta name="pdf:PDFVersion" content="1.5" />
                <meta name="pdf:docinfo:title" content="Project TS" />
                <meta name="xmp:CreatorTool" content="Microsoft® PowerPoint® 2013" />
                <meta name="access_permission:modify_annotations" content="true" />
                <meta name="access_permission:can_print_degraded" content="true" />
                <meta name="dc:creator" content="Okwechime, Jania (UK - London)" />
                <meta name="dcterms:created" content="2017-11-01T15:39:01Z" />
                <meta name="Last-Modified" content="2017-11-01T15:39:01Z" />
                <meta name="dcterms:modified" content="2017-11-01T15:39:01Z" />
                <meta name="dc:format" content="application/pdf; version=1.5" />
                <meta name="Last-Save-Date" content="2017-11-01T15:39:01Z" />
                <meta name="pdf:docinfo:creator_tool" content="Microsoft® PowerPoint® 2013" />
                <meta name="access_permission:fill_in_form" content="true" />
                <meta name="pdf:docinfo:modified" content="2017-11-01T15:39:01Z" />
                <meta name="meta:save-date" content="2017-11-01T15:39:01Z" />
                <meta name="pdf:encrypted" content="false" />
                <meta name="dc:title" content="Project TS" />
                <meta name="modified" content="2017-11-01T15:39:01Z" />
                <meta name="Content-Type" content="application/pdf" />
                <meta name="pdf:docinfo:creator" content="Okwechime, Jania (UK - London)" />
                <meta name="X-Parsed-By" content="org.apache.tika.parser.DefaultParser" />
                <meta name="X-Parsed-By" content="org.apache.tika.parser.pdf.PDFParser" />
                <meta name="creator" content="Okwechime, Jania (UK - London)" />
                <meta name="meta:author" content="Okwechime, Jania (UK - London)" />
                <meta name="meta:creation-date" content="2017-11-01T15:39:01Z" />
                <meta name="created" content="Wed Nov 01 15:39:01 GMT 2017" />
                <meta name="access_permission:extract_for_accessibility" content="true" />
                <meta name="access_permission:assemble_document" content="true" />
                <meta name="xmpTPg:NPages" content="3" />
                <meta name="Creation-Date" content="2017-11-01T15:39:01Z" />
                <meta name="resourceName" content="SAMPLE.pdf" />
                <meta name="access_permission:extract_content" content="true" />
                <meta name="access_permission:can_print" content="true" />
                <meta name="Author" content="Okwechime, Jania (UK - London)" />
                <meta name="producer" content="Microsoft® PowerPoint® 2013" />
                <meta name="access_permission:can_modify" content="true" />
                <meta name="pdf:docinfo:producer" content="Microsoft® PowerPoint® 2013" />
                <meta name="pdf:docinfo:created" content="2017-11-01T15:39:01Z" />
                <title>Project TS</title>
                </head>
                <body><div class="page"><p />
                <p>Project TS
                31/10/2017
                </p>
                <p>Luke Evans
                </p>
                <p>Jania Okwechime
                </p>
                <p>London UK</p>
                <p />
                </div>
                <div class="page"><p />
                <p>Financials
                </p>
                <p>2015 2016 2017
                </p>
                <p>Revenue £17000000 18000000 2000000
                </p>
                <p>Headcount 100 150 200
                </p>
                <p>PDFMiner is a tool for extracting information from PDF documents. Unlike other PDF-related tools, it focuses 
                entirely on getting and analyzing text data. PDFMiner allows one to obtain the exact location of text in a page, as 
                well as other information such as fonts or lines. It includes a PDF converter that can transform PDF files into other 
                text formats (such as HTML). It has an extensible PDF parser that can be used for other purposes than text 
                analysis.</p>
                <p />
                </div>
                <div class="page"><p />
                <p>Continued
                </p>
                <p>• Features
                </p>
                <p>• Written entirely in Python. (for version 2.4 or newer)
                </p>
                <p>• Parse, analyze, and convert PDF documents.
                </p>
                <p>• PDF-1.7 specification support. (well, almost)
                </p>
                <p>• CJK languages and vertical writing scripts support.
                </p>
                <p>• Various font types (Type1, TrueType, Type3, and CID) support.
                </p>
                <p>• Basic encryption (RC4) support.
                </p>
                <p>• PDF to HTML conversion (with a sample converter web app).
                </p>
                <p>• Outline (TOC) extraction.
                </p>
                <p>• Tagged contents extraction.
                </p>
                <p>• Reconstruct the original layout by grouping text chunks.</p>
                <p />
                </div>
                </body></html>

        """
        paragraphs = processor.split_paragraphs(raw_text)

        # ASSERTIONS
        # (b)
        self.assertEqual(59, len(paragraphs))

    def test_no_contents_page(self):
        """
        (c) Verify that the processing does not incorrectly identify a
        contents page

        (d) Verify that the processing will continue even if no contents
        page is found
        """

        processor = processors.PDFProcessor(r"")
        raw_text = """
            <html xmlns="http://www.w3.org/1999/xhtml">
                <head>
                <meta name="date" content="2017-11-01T15:39:01Z" />
                <meta name="pdf:PDFVersion" content="1.5" />
                <meta name="pdf:docinfo:title" content="Project TS" />
                <meta name="xmp:CreatorTool" content="Microsoft® PowerPoint® 2013" />
                <meta name="access_permission:modify_annotations" content="true" />
                <meta name="access_permission:can_print_degraded" content="true" />
                <meta name="dc:creator" content="Okwechime, Jania (UK - London)" />
                <meta name="dcterms:created" content="2017-11-01T15:39:01Z" />
                <meta name="Last-Modified" content="2017-11-01T15:39:01Z" />
                <meta name="dcterms:modified" content="2017-11-01T15:39:01Z" />
                <meta name="dc:format" content="application/pdf; version=1.5" />
                <meta name="Last-Save-Date" content="2017-11-01T15:39:01Z" />
                <meta name="pdf:docinfo:creator_tool" content="Microsoft® PowerPoint® 2013" />
                <meta name="access_permission:fill_in_form" content="true" />
                <meta name="pdf:docinfo:modified" content="2017-11-01T15:39:01Z" />
                <meta name="meta:save-date" content="2017-11-01T15:39:01Z" />
                <meta name="pdf:encrypted" content="false" />
                <meta name="dc:title" content="Project TS" />
                <meta name="modified" content="2017-11-01T15:39:01Z" />
                <meta name="Content-Type" content="application/pdf" />
                <meta name="pdf:docinfo:creator" content="Okwechime, Jania (UK - London)" />
                <meta name="X-Parsed-By" content="org.apache.tika.parser.DefaultParser" />
                <meta name="X-Parsed-By" content="org.apache.tika.parser.pdf.PDFParser" />
                <meta name="creator" content="Okwechime, Jania (UK - London)" />
                <meta name="meta:author" content="Okwechime, Jania (UK - London)" />
                <meta name="meta:creation-date" content="2017-11-01T15:39:01Z" />
                <meta name="created" content="Wed Nov 01 15:39:01 GMT 2017" />
                <meta name="access_permission:extract_for_accessibility" content="true" />
                <meta name="access_permission:assemble_document" content="true" />
                <meta name="xmpTPg:NPages" content="3" />
                <meta name="Creation-Date" content="2017-11-01T15:39:01Z" />
                <meta name="resourceName" content="SAMPLE.pdf" />
                <meta name="access_permission:extract_content" content="true" />
                <meta name="access_permission:can_print" content="true" />
                <meta name="Author" content="Okwechime, Jania (UK - London)" />
                <meta name="producer" content="Microsoft® PowerPoint® 2013" />
                <meta name="access_permission:can_modify" content="true" />
                <meta name="pdf:docinfo:producer" content="Microsoft® PowerPoint® 2013" />
                <meta name="pdf:docinfo:created" content="2017-11-01T15:39:01Z" />
                <title>no name</title>
                </head>
                <body>
                <div class="page">
                <p />
                <p>no date
                </p>
                <p>Luke Evans
                </p>
                <p>Jania Okwechime
                </p>
                <p>London UK</p>
                <p />
                </div>
                <div class="page">
                <p />
                <p>Financials
                </p>
                <p>2015 2016 2017
                </p>
                <p>Revenue £17000000 18000000 2000000
                </p>
                <p>Headcount 100 150 200
                </p>
                <p>PDFMiner is a tool for extracting information from PDF documents. Unlike other PDF-related tools, it focuses 
                entirely on getting and analyzing text data. PDFMiner allows one to obtain the exact location of text in a page, as 
                well as other information such as fonts or lines. It includes a PDF converter that can transform PDF files into other 
                text formats (such as HTML). It has an extensible PDF parser that can be used for other purposes than text 
                analysis.</p>
                <p />
                </div>
                <div class="page">
                <p />
                <p>Continued
                </p>
                <p>• Features
                </p>
                <p>• Written entirely in Python. (for version 2.4 or newer)
                </p>
                <p>• Parse, analyze, and convert PDF documents.
                </p>
                <p>• PDF-1.7 specification support. (well, almost)
                </p>
                <p>• CJK languages and vertical writing scripts support.
                </p>
                <p>• Various font types (Type1, TrueType, Type3, and CID) support.
                </p>
                <p>• Basic encryption (RC4) support.
                </p>
                <p>• PDF to HTML conversion (with a sample converter web app).
                </p>
                <p>• Outline (TOC) extraction.
                </p>
                <p>• Tagged contents extraction.
                </p>
                <p>• Reconstruct the original layout by grouping text chunks.</p>
                <p />
                </div>
                </body></html>
        """
        paragraphs = processor.split_paragraphs(raw_text)
        processor.process_paragraphs(paragraphs)
        pages = {
            1: ['no date', 'Luke Evans', 'Jania Okwechime', 'London UK'],
            2: ['Financials', '2015 2016 2017',
                'Revenue £17000000 18000000 2000000',
                'Headcount 100 150 200',
                'PDFMiner is a tool for extracting information from PDF '
                'documents. Unlike other PDF-related tools, it '
                'focuses \n                entirely on getting and '
                'analyzing text data. PDFMiner allows one to obtain the '
                'exact location of text in a page, as \n                '
                'well as other information such as fonts or lines. It '
                'includes a PDF converter that can transform PDF files into '
                'other \n                text formats (such as HTML). It has '
                'an extensible PDF parser that can be used for other purposes '
                'than text \n                analysis.'],
            3: ['Continued', '• Features', '• Written entirely in Python. '
                                           '(for version 2.4 or newer)',
                '• Parse, analyze, and convert PDF documents.', '• PDF-1.7 '
                'specification support. (well, almost)',
                '• CJK languages and vertical writing scripts support.',
                '• Various font types (Type1, TrueType, Type3, '
                'and CID) support.',
                '• Basic encryption (RC4) support.',
                '• PDF to HTML conversion (with a sample converter web app).',
                '• Outline (TOC) extraction.',
                '• Tagged contents extraction.',
                '• Reconstruct the original layout by grouping text chunks.']
        }

        # ASSERTIONS
        # (c)
        self.assertEqual(processor.contents, {})
        # (d)
        self.assertEqual(processor.pages, pages)

    def test_read__empty_pdf(self):
        """
        (e) Verify that when reading a non existant file, read_pdf returns None
        """

        processor = processors.PDFProcessor(os.path.join(test_dir,
                                                         'DOES_NOT_EXIST.txt'))
        text = processor.read_pdf(server)

        # ASSERTIONS
        # (d)
        self.assertIsNone(text)

    def test_page_contents_extraction(self):
        """
        (f) Verify that the processing identifies the correct sentences to
        be potential contents lines
        """

        processor = processors.PDFProcessor(r"")
        paragraphs = [
            "Page 0",
            '<div class="page">',
            "Project Happy 12",
            "this is the first page it has some contents on it",

            "Contents 1",

            """Second Section 2
            Third Section 8""",

            "Rogue Section 4",

            "Final Section 20",

        ]

        processor.process_paragraphs(paragraphs)
        output = processor.page_contents

        expected = [
            ("Project Happy", 12),
            ("Contents", 1),
            ("Second Section", 2),
            ("Third Section", 8),
            ("Rogue Section", 4),
            ("Final Section", 20),
        ]

        # ASSERTIONS
        # (e)
        self.assertEqual(expected, output)


class ParagraphProcessorTest(unittest.TestCase):
    """
    2. Paragraph Processing
    """

    def test_extraction_success_check(self):
        """
        (a) Verify that extraction_successful returns False if the
        paragraph is messy
        """

        processor = processors.ParagraphProcessor(
            """.'02-(%"("4,0('(-4*,')("0(.'02$05(4*")3&%-("""
        )
        output = processor.extraction_successful

        # ASSERTIONS
        # (a)
        self.assertEqual(False, output)

    def test_check_if_page_marker(self):
        """
        (b) Verify that page_marker correctly identifies a page marker

        (c) Verify that page_marker increases the page number by 1
        """

        processor = processors.ParagraphProcessor('<div class="page">')
        expected = processor.page_number + 1
        output = processor.check_if_page_marker()

        # ASSERTIONS
        # (b) QC0
        self.assertEqual(True, output)
        # (c)
        self.assertEqual(expected, processor.page_number)

    def test_check_if_page_marker2(self):
        """
        (d) Verify that page_marker does not return true for false
        positives

        (e) Verify that page_marker does not tick the page number up
        for false positives
        """
        processor = processors.ParagraphProcessor('<div clasafwafs="page">')
        starting_page_number = processor.page_number
        output = processor.check_if_page_marker()

        # QC1
        processor1 = processors.ParagraphProcessor('<div class="container">')
        output1 = processor1.check_if_page_marker()

        processor2 = processors.ParagraphProcessor('<div class="nav">')
        output2 = processor2.check_if_page_marker()

        # ASSERTIONS
        # (d)
        self.assertEqual(False, output)
        # (d) QC1
        self.assertEqual(False, output1)
        self.assertEqual(False, output2)
        # (e)
        self.assertEqual(starting_page_number, processor.page_number)
        # (e) QC1
        self.assertEqual(starting_page_number, processor1.page_number)
        self.assertEqual(starting_page_number, processor2.page_number)

    def test_search_for_project_name(self):
        """
        (f) Verify that search_for_project_name correctly identifies the
        project name
        """
        processor = processors.ParagraphProcessor('Project Dynamics27')
        processor.page_number = 27
        project_name = processor.search_for_project_name()

        # ASSERTIONS
        # (f)
        self.assertEqual("Project Dynamics", project_name)

    def test_search_for_project_date(self):
        """
        (g) Verify that search_for_project_date correctly identifies a
        project date
        """

        processor = processors.ParagraphProcessor('01 June 2015')
        project_date = processor.search_for_project_date()

        # ASSERTIONS
        # (g)
        self.assertEqual('01 June 2015', project_date)

    def test_single_contents_line(self):
        """
        (h) Verify that a single contents line is correct picked up by
        check_for_contents
        """

        processor = processors.ParagraphProcessor('Contents 3')
        contents_lines = processor.check_for_contents_lines()

        # ASSERTIONS
        # (h)
        self.assertEqual([("Contents", 3)], contents_lines)

    def test_multiple_contents_lines(self):
        """
        (i) Verifies that multiple contents lines are correctly picked
        up by check_for_contents_lines
        """

        processor = processors.ParagraphProcessor(
            'Contents 3\n    Balance Sheet 5\n       Income Statement 8'
        )
        contents_lines = processor.check_for_contents_lines()

        # ASSERTIONS
        # (i)
        self.assertEqual(
            [
                ("Contents", 3),
                ("Balance Sheet", 5),
                ("Income Statement", 8)
            ],
            contents_lines
        )

    def test_search_for_page_name_clean(self):
        """
        (j) Verify that search_for_page_name correctly identifies a page
        name
        """

        processor = processors.ParagraphProcessor("Executive summary | Overall Conclusions")
        processor.page_number = 4
        page_name = processor.search_for_page_name()
        expected = "Overall Conclusions"
        output = page_name

        # ASSERTIONS
        # (j)
        self.assertEqual(expected, output)

    def test_search_for_page_name_clean_page_number(self):
        """
        (k) Verify that search_for_page_name still returns the correct page
        name in the instance that the page number is appended to the
        pattern
        """

        processor = processors.ParagraphProcessor("5Executive summary | Overall Conclusions5")
        processor.page_number = 5
        page_name = processor.search_for_page_name()
        expected = "Overall Conclusions"
        output = page_name

        # ASSERTIONS
        # (k)
        self.assertEqual(expected, output)

    def test_search_for_page_name_ugly(self):
        """
        (l) Verify that search_for_page_name still returns the correct
        page name in the instance that the page name is attached to
        a longer string
        """

        processor = processors.ParagraphProcessor("""
        Project Admiral – Seller’s Information Document - 01 June 201512Executive summary | Customers & Products
        """)
        processor.page_number = 12
        page_name = processor.search_for_page_name()
        expected = "Customers & Products"
        output = page_name

        # ASSERTIONS
        # (l)
        self.assertEqual(expected, output)

    # QC1

    def test_extraction_success_check_QC1(self):
        """
        (a) Verify that extraction_successful returns False if the
        paragraph is messy

        Expand test_extraction_success_check
        """

        processor = processors.ParagraphProcessor(
            """.'02-(%"("4,0('(-4*,')("0(.'02$05(4*")3&%-("""
        )
        output = processor.extraction_successful

        processor_good = processors.ParagraphProcessor(
            """Here are some real words"""
        )
        output_good = processor_good.extraction_successful

        processor_mid = processors.ParagraphProcessor(
            """He*r_e are s%me re&l word5"""
        )
        output_mid = processor_mid.extraction_successful
        # ASSERTIONS
        self.assertEqual(False, output)
        self.assertEqual(True, output_good)
        self.assertEqual(True, output_mid)

    def test_search_for_project_date_QC1(self):
        """
        (g) Verify that search_for_project_date correctly identifies a
        project date
        """

        processor = processors.ParagraphProcessor('01 June 201598')
        project_date = processor.search_for_project_date()

        self.assertEqual('01 June 2015', project_date)


class ContentsProcessorTest(unittest.TestCase):
    """
    3. Contents Processing
    """

    def test_validation_contents(self):
        """
        (a) Verify that validate_contents_lines correctly identifies the
        page adjustment for a simple contents page declared scenario

        (b) Verify that validate_contents_lines correctly identifies the
        adjustment boundary for a simple contents page declared scenario

        (c) Verify that validate_contents_lines correctly identifies the
        valid contents lines with cleansed section names for a simple contents page declared
        scenario
        """
        pdf_processor = processors.PDFProcessor("")
        pdf_processor.project_name = "Project Happy"
        pdf_processor.number_of_pages = 16

        contents_processor = processors.ContentsProcessor(pdf_processor)

        page_contents = [
            ("Project Happy", 12),
            ("Contents...", 1),
            ("Second Section", 2),
            ("Third Section", 8),
            ("Too Low Section", 4),
            ("Too Large Section", 20),
        ]

        contents_processor.validate_contents_lines(page_contents, 1)
        output = contents_processor.validated
        expected = [
            ("Contents", 1),
            ("Second Section", 2),
            ("Third Section", 8),
        ]

        # ASSERTIONS
        # (a)
        self.assertEqual([0, ], contents_processor.page_adjustment)
        # (b)
        self.assertEqual([1, ], contents_processor.adjustment_boundaries)
        # (c)
        self.assertEqual(expected, output)

    def test_validation_no_contents(self):
        """
        (d) Verify that validate_contents_lines correctly identifies the
        page adjustment for a simple no contents page declared scenario

        (e) Verify that validate_contents_lines correctly identifies the
        adjustment boundary for a simple no contents page declared
        scenario

        (f) Verify that validate_contents_lines correctly identifies the
        valid contents lines for a simple no contents page declared
        scenario
        """
        pdf_processor = processors.PDFProcessor("")
        pdf_processor.project_name = "Project Happy"
        pdf_processor.number_of_pages = 16

        contents_processor = processors.ContentsProcessor(pdf_processor)

        page_contents = [
            ("Project Happy", 12),
            ("First Section", 1),
            ("Second Section", 2),
            ("Third Section", 8),
            ("Too Low Section", 4),
            ("Too Large Section", 20),
        ]

        contents_processor.validate_contents_lines(page_contents, 1)
        output = contents_processor.validated
        expected = [
            ("First Section", 1),
            ("Second Section", 2),
            ("Third Section", 8),
        ]

        # ASSERTIONS
        # (d)
        self.assertEqual([1, ], contents_processor.page_adjustment)
        # (e)
        self.assertEqual([1, ], contents_processor.adjustment_boundaries)
        # (f)
        self.assertEqual(expected, output)

    def test_validation_contents_overflow(self):
        """
        --overflowing means there is a contents page that is spread over
        more than one page of the document

        (g) Verify that validate_contents_lines correctly identifies the
        page adjustment for a contents page declared
        overflowing scenario

        (h) Verify that validate_contents_lines correctly identifies the
        adjustment boundary for a simple contents page declared
        overflowing scenario

        (i) Verify that validate_contents_lines correctly identifies the
        valid contents lines for a simple contents page declared
        overflowing scenario
        """
        pdf_processor = processors.PDFProcessor("")
        pdf_processor.project_name = "Project Happy"
        pdf_processor.number_of_pages = 22

        contents_processor = processors.ContentsProcessor(pdf_processor)

        first_page_contents = [
            ("Project Happy", 12),
            ("Contents", 1),
            ("Second Section", 3),
            ("Third Section", 8),
            ("Too Low Section", 4),
            ("Too Large Section", 30),
        ]

        second_page_contents = [
            ("Fourth Section", 13),
            ("Fifth Section", 16),
            ("Sixth Section", 18),
        ]

        contents_processor.validate_contents_lines(first_page_contents, 1)
        contents_processor.validate_contents_lines(second_page_contents, 2)

        output = contents_processor.validated
        expected = [
            ("Contents", 1),
            ("Second Section", 3),
            ("Third Section", 8),
            ("Fourth Section", 13),
            ("Fifth Section", 16),
            ("Sixth Section", 18),
        ]

        # ASSERTIONS
        # (g)
        self.assertEqual([0, ], contents_processor.page_adjustment)
        # (h)
        self.assertEqual([2, ], contents_processor.adjustment_boundaries)
        # (i)
        self.assertEqual(expected, output)

    def test_validation_no_contents_overflow(self):
        """
        (j) Verify that validate_contents_lines correctly identifies the
        page adjustment for a no contents page declared, overflowing
        scenario

        (k) Verify that validate_contents_lines correctly identifies the
        adjustment boundary for a no contents page declared, overflowing
        scenario

        (l) Verify that validate_contents_lines correctly identifies the
        valid contents lines for a no contents page declared,
        overflowing scenario
        """
        pdf_processor = processors.PDFProcessor("")
        pdf_processor.project_name = "Project Happy"
        pdf_processor.number_of_pages = 22

        contents_processor = processors.ContentsProcessor(pdf_processor)

        first_page_contents = [
            ("Project Happy", 12),
            ("First Section", 1),
            ("Second Section", 5),
            ("Third Section", 8),
            ("Too Low Section", 4),
            ("Too Large Section", 30),
        ]

        second_page_contents = [
            ("Fourth Section", 13),
            ("Fifth Section", 16),
            ("Sixth Section", 18),
        ]

        contents_processor.validate_contents_lines(first_page_contents, 1)
        contents_processor.validate_contents_lines(second_page_contents, 2)

        output = contents_processor.validated
        expected = [
            ("First Section", 1),
            ("Second Section", 5),
            ("Third Section", 8),
            ("Fourth Section", 13),
            ("Fifth Section", 16),
            ("Sixth Section", 18),
        ]

        # ASSERTIONS
        # (j)
        self.assertEqual([2, ], contents_processor.page_adjustment)
        # (k)
        self.assertEqual([2, ], contents_processor.adjustment_boundaries)
        # (l)
        self.assertEqual(expected, output)

    def test_validation_contents_amended(self):
        """
        --amended means there is more than one separate contents page

        (m) Verify that validate_contents_lines correctly identifies the
        page adjustment for a contents page declared, amended scenario

        (n) Verify that validate_contents_lines correctly identifies the
        adjustment boundary for a contents page declared, amended
        scenario

        (o) Verify that validate_contents_lines correctly identifies the
        valid contents lines for a contents page declared, amended
        scenario
        """

        pdf_processor = processors.PDFProcessor("")
        pdf_processor.project_name = "Project Happy"
        pdf_processor.number_of_pages = 40

        contents_processor = processors.ContentsProcessor(pdf_processor)

        first_page_contents = [
            ("Project Happy", 12),
            ("Contents", 1),
            ("Second Section", 3),
            ("Third Section", 8),
            ("Too Low Section", 4),
            ("Too Large Section", 60),
        ]

        second_page_contents = [
            ("Fourth Section", 13),
            ("Fifth Section", 16),
            ("Sixth Section", 18),
        ]

        contents_processor.validate_contents_lines(first_page_contents, 1)
        contents_processor.validate_contents_lines(second_page_contents, 12)

        output = contents_processor.validated
        expected = [
            ("Contents", 1),
            ("Second Section", 3),
            ("Third Section", 8),
            ("Fourth Section", 13),
            ("Fifth Section", 16),
            ("Sixth Section", 18),
        ]

        # ASSERTIONS
        # (m)
        self.assertEqual(expected, output)
        # (n)
        self.assertEqual([0], contents_processor.page_adjustment)
        # (o)
        self.assertEqual([1], contents_processor.adjustment_boundaries)

    def test_validation_no_contents_amended(self):
        """
        (p) Verify that validate_contents_lines correctly identifies the
        page adjustment for a contents page declared, amended scenario

        (q) Verify that validate_contents_lines correctly identifies the
        adjustment boundary for a no contents page declared, amended
        scenario

        (r) Verify that validate_contents_lines correctly identifies the
        valid contents lines for a no contents page declared, amended
        scenario
        """

        pdf_processor = processors.PDFProcessor("")
        pdf_processor.project_name = "Project Happy"
        pdf_processor.number_of_pages = 40

        contents_processor = processors.ContentsProcessor(pdf_processor)

        first_page_contents = [
            ("Project Happy", 12),
            ("First Section", 1),
            ("Second Section", 3),
            ("Third Section", 8),
            ("Too Low Section", 4),
            ("Too Large Section", 60),
        ]

        second_page_contents = [
            ("Fourth Section", 13),
            ("Fifth Section", 16),
            ("Sixth Section", 18),
        ]

        contents_processor.validate_contents_lines(first_page_contents, 1)
        contents_processor.validate_contents_lines(second_page_contents, 12)

        output = contents_processor.validated
        expected = [
            ("First Section", 1),
            ("Second Section", 3),
            ("Third Section", 8),
            ("Fourth Section", 13),
            ("Fifth Section", 16),
            ("Sixth Section", 18),
        ]

        # ASSERTIONS
        # (p)
        self.assertEqual(expected, output)
        # (q)
        self.assertEqual([1], contents_processor.page_adjustment)
        # (r)
        self.assertEqual([1], contents_processor.adjustment_boundaries)


if __name__ == '__main__':
    unittest.main()
