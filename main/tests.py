from django.test import TestCase
from main import models as md
from django.contrib.auth.models import User

# Method Testing
class FileTest(TestCase):
    """
    1. File Methods
    """

    def test_pdf_name(self):
        """
        (a) Verify that pdf_name returns the name of the file with .pdf
        appended
        """

        mock = md.File(name="sample")

        # ASSERTIONS
        # (a)
        self.assertEqual("sample.pdf", mock.pdf_name())

    def test_index_name(self):
        """
        (b) Verify that index_name returns the cleaned version of the
        name of the file
        """

        mock = md.File(name="SamplePDFWith horrible naming stuff")

        # ASSERTIONS
        # (b)
        self.assertEqual(
            "samplepdfwith_horrible_naming_stuff", mock.index_name()
        )

    def test_find_sub_sections(self):
        """
        (c) Verify that find sub_sections returns all the Sections of
        the document a list of tuples, with the tuples containing
        the Section and a list of any page names/sub-section.
        """

        mock, created = md.File.create(name="sample")
        mock.save()
        mock_sections = []
        page_number = 0
        # this loop compiles the list that should be returned by the
        # method. It also creates the dummy sections
        for i in range(0, 3):
            mock_section, created = md.Section.create(
                file=mock,
                name="sample_section{0}".format(i),
                first_page=i * 4,
                last_page=(i + 1) * 4 - 1
            )
            mock_section.save()
            mock_page_names = []
            for j in range(0, 3):
                mock_page, created = md.Page.create(file=mock,
                                                    page_number=page_number)
                mock_page.page_name = "page_{0}".format(j)
                mock_page_names.append(mock_page.page_name)
                mock_page.section = mock_section
                mock_page.save()
                page_number += 1
            mock_sections.append((mock_section, mock_page_names))

        expected = mock_sections
        output = mock.find_sub_sections()

        # ASSERTIONS
        # (c)
        self.assertEqual(expected, output)


class PageTest(TestCase):
    """
    2. Page Methods
    """

    def test_link(self):
        """
        (a) Verify that test_link returns the hyperlink to the right
        page in the PDF.
        """

        mock = md.Page(page_number=0, file=md.File(name="sample"))

        # ASSERTIONS
        # (a)
        self.assertEqual("\\static\\sample#page=0", mock.link())


class StoredSearchTest(TestCase):
    """
    3. StoredSearch Methods
    """

    def test_find_by_keywords(self):
        """
        (a) Verify that find_by_keywords returns the StoredSearch that
        best matches the keywords given for found_search1

        (b) Verify that find_by_keywords returns the StoredSearch that
        best matches the keywords given for found_search2
        """
        for keyword in ["one", "two", "three", "four", "five"]:
            md.Keyword.create(keyword)

        keywords_list = md.Keyword.objects.all()

        dummy_type = "dummy"
        dummy_sub_type = "dummied"
        for i in range(3):
            md.StoredSearch.create(
                keywords=keywords_list[i:i + 2],
                description="{0}".format(i),
                search_type=dummy_type,
                sub_type=dummy_sub_type,
            )

        found_search1 = md.StoredSearch.find_by_keywords(keywords_list[0:1])
        found_search2 = md.StoredSearch.find_by_keywords([keywords_list[3],
                                                          keywords_list[4]])

        # ASSERTIONS
        # (a)
        self.assertEqual("0", found_search1.description)
        # (b)
        self.assertEqual("2", found_search2.description)

    def test_keywords_list(self):
        """
        (c) Verify that keywords_list returns a list of all the keywords
        that are involved in the search.
        """

        mock = md.StoredSearch.objects.create(id=1)
        for i in range(1, 5):
            mock_keyword = md.Keyword.objects.create(keyword=str(i))
            mock.keywords.add(mock_keyword)

        # ASSERTIONS
        # (c)
        self.assertEqual(["1", "2", "3", "4"], mock.keyword_list())


# Database Testing
class KeywordDBTest(TestCase):
    """
    2. Keyword Tables

    These are tests to check that the Keyword model is working as
    desired.

    These tests are supplementary to the SQL testing that was
    executed in QC0. For those tests please refer to the Database QC
    Documentation file.
    """
    def test_keyword_set_creation_and_alt_list(self):
        """
        (a) Verify that the creation of a keyword set creates each keyword
        in the set.

        (b) Verify that the created keywords are all created as alternatives
        of each other.

        (c) Verify that for each alternative relationship, the relationship
        exists both ways.
        """

        keyword_set = md.Keyword.create_keyword_set(["word1", "word2", "word3",
                                                     "word4"])

        for i, keyword in enumerate(keyword_set):

            # ASSERTIONS
            # (a)
            self.assertEqual(keyword_set[:i] + keyword_set[i + 1:],
                             list(keyword.alternatives.all()))
            # (b) and (c)
            self.assertEqual(
                sorted(
                    keyword_set,
                    key=lambda key: key.keyword
                ),
                sorted(
                    keyword.alt_list(),
                    key=lambda key: key.keyword
                )
            )
            keyword.save()


class ResultDBTest(TestCase):
    """
    3. Results Tables

    These are tests to ensure that the desired transactions occur on
    creation, submission and clearing of Results.

    These tests are supplementary to the SQL testing that was
    executed in QC0. For those tests please refer to the Database QC
    Documentation file.
    """

    def setUp(self):
        """
        This creates the dummy data that is needed for creating a
        ModelResult
        """

        super().setUp()
        self.dummy_file, created = md.File.create("file")
        self.dummy_search = md.StoredSearch.create(["keyword"], "search",
                                                   "", "")

        self.dummy_result = md.Result.create(file=self.dummy_file,
                                             search=self.dummy_search,
                                             timestamp_group_default="FY14",
                                             unit_group_default="£",
                                             timestamp_group="FY",
                                             unit_group="Currency")
        self.dummy_page, created = md.Page.create(self.dummy_file, 20)

    def test_create_result(self):
        """
        The creation of the result occurs in the setUp method above.

        (a) Verify that on creation of a result the related UnitGroup is
        also created with the correct unit as given.

        (b) Verify that on creation of a result the related
        TimestampGroup is also created with the correct timestamp
        as given.

        """

        u_group = md.UnitGroup.objects.get(name="Currency")
        ts_group = md.TimestampGroup.objects.get(name="FY")

        # ASSERTIONS
        # (a)
        self.assertEqual(u_group.unit, "£")
        # (b)
        self.assertEqual(ts_group.timestamp, "FY14")

    def test_submit_result(self):
        """
        (c) Verify that on submission of a result the unit for
        the related UnitGroup updates to match the submitted result.

        (d) Verify that on submission of a result the timestamp for
        the related TimestampGroup updates to match the submitted result.

        (e) Verify that on submission of a result the value given for
        the result is added as the result value

        (f) Verify that on submission of a result, the page that result
        was found on updates to having had a previous match.
        """
        self.dummy_user = User.objects.create_user('Dummy User', 'User@dummy.com', 'password')
        self.dummy_result.submit(value=11, units="$", timestamp="FY15",
                                 page=self.dummy_page, user=User.objects.all()[0])

        # ASSERTIONS
        # (c)
        self.assertEqual("$", md.UnitGroup.objects.get(name="Currency").unit)
        # (d)
        self.assertEqual("FY15", md.TimestampGroup.objects.get(
            name="FY").timestamp)
        # (e)
        self.assertEqual(11, self.dummy_result.result)
        # (f)
        self.assertEqual(True, self.dummy_page.previous_match)

    def test_clear_result(self):
        """
        (g) Verify that on clearing a result, the results value reverts
        to None

        (h) Verify that on clearing a result, the results units reverts
        to None

        (i) Verify that on clearing a result, the results timestamp
        reverts to None

        (j) Verify that on clearing the final populated result in a
        UnitGroup the unit for that UnitGroup reverts to the default

        (k) Verify that on clearing the final populated result in a
        TimestampGroup the timestamp for thatTimestampGroup reverts to
        the default

        """
        self.dummy_user = User.objects.create_user('Dummy User', 'User@dummy.com', 'password')
        self.dummy_result.submit(value=11, units="$", timestamp="FY15",
                                 page=self.dummy_page, user=User.objects.all()[0])
        self.dummy_result.clear()

        # ASSERTIONS
        # (g)
        self.assertEqual(None, self.dummy_result.result)
        # (h)
        self.assertEqual(None, self.dummy_result.unit)
        # (i)
        self.assertEqual(None, self.dummy_result.timestamp)
        # (j)
        self.assertEqual("£", md.UnitGroup.objects.get(name="Currency").unit)
        # (k)
        self.assertEqual("FY14", md.TimestampGroup.objects.get(
            name="FY").timestamp)
