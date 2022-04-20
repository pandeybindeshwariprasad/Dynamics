import re
import datetime

from django.contrib.auth.models import User
from django.db import models
import pyodbc
from numpy.distutils.command.develop import develop

from Deloitte_Dynamics.settings import PATH_TO_SEARCH_LISTS, PRINT_STATEMENT


# Create your models here.
class File(models.Model):
    """
    A model to represent a single document.

    Fields:
        name: a CharField for the document name without the folder path
        project_name: A CharField for the project this document was
                      found to be for
        date: A CharField for the date this document was completed.
              This is a CharField as it needs to mirror the string that
              is found in the document.
        num_pages: a IntegerField to show the number of pages in this
                   document
    """

    name = models.CharField(max_length=255, primary_key=True)
    project_name = models.CharField(max_length=120, blank=True, null=True)
    date = models.CharField(max_length=120, blank=True, null=True)
    num_pages = models.IntegerField(null=True, blank=True)
    company_description = models.CharField(max_length=255, null=True, blank=True)
    # Extra fileds:
    source_country = models.CharField(max_length=100, default='GBR')
    opration_country = models.CharField(max_length=100, default='GBR')

    def pdf_name(self):
        """
        Appends the pdf end tag to this documents name
        (This is for ease of use)

        Returns:
            the name of the document with pdf appended onto the end

        """
        return "{0}.pdf".format(self.name)

    def index_name(self):
        """
        Returns the name of the document without any characters that are
        not accepted by elasticsearch

        These characters are (/.*<|>?', -)

        Returns: The filtered clean name of the document

        """
        return re.sub(r"[/.*<|>?', -]+", "_", self.name).lower()

    def find_sub_sections(self):
        """
        For each section related to this file, find all the associated
        page names within that section and return the group

        Returns:
            A list of tuples (section, page names in that section)

        """

        sections = Section.objects.filter(file=self)
        section_zip = []
        for section in sections:
            page_names = section.page_set.values_list('page_name')
            unique_page_names = []
            for page_name in page_names:
                page_name = page_name[0]
                if page_name:
                    if page_name not in unique_page_names:
                        unique_page_names.append(page_name)
            section_zip.append((section, unique_page_names))

        # EXCEPTION FOR POORLY EXTRACTED CONTENTS PAGES

        return section_zip

    @classmethod
    def create(cls, name):
        """
        If this file has not already been created, create this file

        This is to avoid duplicating files

        Args:
            name: the name of the document that is being created

        Returns: the file that is created/found and a boolean detailing
                 if this is a new file

        """
        file, created = cls.objects.get_or_create(name=name)
        # add company description
        if created:
            # ------------ start  ---------------- #
            # Create new db connection
            conn = pyodbc.connect('Driver={SQL Server};'
                                  'Server=UKVIRCI00210;'
                                  'Database=UK429_Dynamics_Test;'
                                  'Trusted_Connection=yes;')

            cursor = conn.cursor()
            cursor.execute('SELECT * FROM company_descriptor')

            #
            current_file_name = name[0:9]
            current_file_code = current_file_name.replace('_', '-')
            # print("current_file_code: ", current_file_code)
            for row in cursor:
                # print(row.Project)
                if current_file_code == row.Project:
                    file.company_description = row.CompanyDescription
                    file.save()
                    break
            # ------------ end  ---------------- #
            # current_file_name = name[0:9]
            # get_all_obj = cls.objects.all()
            # for obj in get_all_obj:
            #     if str(obj.name).startswith(current_file_name):
            #         print(obj.name, ': ', obj.company_description)
            #         file.company_description = obj.company_description
            #         file.save()
            #         break
        return file, created

    def __str__(self):
        return self.name


class Section(models.Model):
    """
    A model to represent a section of a document.

    Fields:
        name: a CharField for the name of this section
        file: a foreign key to the file this section came from
        first_page: the first page of this section
        last_page: the last page of this section

    """

    name = models.CharField(max_length=120)
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    first_page = models.IntegerField()
    last_page = models.IntegerField()

    @classmethod
    def create(cls, file, name, first_page, last_page):
        """
        If this section has not already been created, create this section

        This is to avoid duplicating sections

        Args:
            name: a CharField for the name of this section
            file: a foreign key to the file this section came from
            first_page: the first page of this section
            last_page: the last page of this section

        Returns: the section that is created/found and a boolean detailing
                 if this is a new section

        """
        section, created = cls.objects.get_or_create(file=file,
                                                     name=name,
                                                     first_page=first_page,
                                                     last_page=last_page)
        return section, created

    def __str__(self):
        return str(self.name)


class Page(models.Model):
    """
    A model to represent a page in a section in a file

    Field:
        page_number: an IntegerField for the the page number of this page
                     within the file
        file: a ForeignKey to the file this page came from
        section: a ForeighKey to the section this page came from
        page_name: a CharField for the name that was found for this page
        previous_match: a BooleanField to show whether a result has been
                        found on this page

    """

    page_number = models.IntegerField()
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    # the section this page sits in
    section = models.ForeignKey(Section, on_delete=models.CASCADE, blank=True,
                                null=True, default=None)
    # the page name that was found on the page
    page_name = models.CharField(max_length=255, blank=True, null=True)
    previous_match = models.BooleanField(default=False)

    @classmethod
    def create(cls, file, page_number):
        """
        If this page has not already been created, create this page
        Args:
            file: the file this page is from
            page_number: the page number of the page

        Returns:
            The page that is created/found and a boolean detailing
            if this is a new page

        """
        page, created = cls.objects.get_or_create(file=file,
                                                  page_number=page_number)
        return page, created

    def link(self):
        """
        Returns:
            A hyperlink that opens this page in view
        """
        return "\\static\\{0}#page={1}".format(self.file.name,
                                               self.page_number)

    def __str__(self):
        return str(self.page_number)


class Keyword(models.Model):
    """
    A model to represent a keyword for searching

    Fields:
        keyword: a CharField for the keyword
        alternatives: a ManyToManyField for each keyword this keyword is
                      a synonym for

    """

    keyword = models.CharField(max_length=120, primary_key=True)
    alternatives = models.ManyToManyField("self", blank=True, related_name="+")

    @classmethod
    def create(cls, keyword):
        """
        If this keyword has not already been created, create this
        keyword

        Args:
            keyword: the keyword to be created

        Returns: the keyword that is created/found and a boolean detailing
                 if this is a new keyword

        """

        keyword = str(keyword).lower()
        if len(keyword.strip()) > 0:
            keyword, created = cls.objects.get_or_create(keyword=keyword)
            return keyword, created
        else:
            return None, False

    @classmethod
    def create_keyword_set(cls, keyword_set):
        """
        Create a set of keywords, all of which are synonyms
        Args:
            keyword_set: the set of synonyms to be created

        Returns:
            A list of the created keyword models

        """

        keyword_model_set = []
        created_set = []
        for keyword in keyword_set:
            keyword_model, created = cls.create(keyword)
            if keyword_model:
                keyword_model_set.append(keyword_model)
            if created:
                created_set.append(keyword_model)
        count = 0
        for keyword in keyword_model_set:
            for other_keyword in keyword_model_set:
                if keyword != other_keyword:
                    count = count + 1
                    keyword.alternatives.add(other_keyword)
            keyword.save()

        return created_set

    def alt_list(self, string=False):
        """
        An inclusive list of this keyword and all of its alternatives
        Args:
            string: whether or not to return strings or models

        Returns:
            A list of (string or model)s that represent all of the
            synonyms in the set this keyword belongs to
        """

        alts = self.alternatives.all()
        alt_list = []
        if string:
            alt_list.extend([keyword.keyword.lower() for keyword in alts])
            alt_list.append(self.keyword.lower())
        else:
            alt_list.extend(alts)
            alt_list.append(self)
        return alt_list

    def __str__(self):
        return self.keyword


class SapData(models.Model):
    """
        A model to upload SAP file

        Fields:

        """
    # TODO: ABSOLUTELY SORT THIS OUT

    year = models.CharField(max_length=255, null=True, blank=True)
    billing_partner = models.CharField(max_length=255, null=True, blank=True)
    master_profit_centre = models.CharField(max_length=255, null=True, blank=True)
    project = models.CharField(max_length=255, null=True, blank=True)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    project_customer_no = models.CharField(max_length=255, null=True, blank=True)
    project_customer = models.CharField(max_length=255, null=True, blank=True)
    g_m_uhc = models.CharField(max_length=255, null=True, blank=True)
    cust_industry = models.CharField(max_length=255, null=True, blank=True)
    g_m_pe = models.CharField(max_length=255, null=True, blank=True)
    g_m_uhc_industry = models.CharField(max_length=255, null=True, blank=True)
    g_m_uhc_subindustry = models.CharField(max_length=255, null=True, blank=True)
    sector = models.CharField(max_length=255, null=True, blank=True)
    industry = models.CharField(max_length=255, null=True, blank=True)
    customer_type = models.CharField(max_length=255, null=True, blank=True)
    slc_code = models.CharField(max_length=255, null=True, blank=True)
    g_m_uhc_segmt = models.CharField(max_length=255, null=True, blank=True)
    uhc = models.CharField(max_length=255, null=True, blank=True)
    uhc_number = models.CharField(max_length=255, null=True, blank=True)
    gross_revenue = models.CharField(max_length=255, null=True, blank=True)
    provisions = models.CharField(max_length=255, null=True, blank=True)
    net_services = models.CharField(max_length=255, null=True, blank=True)
    product_sales = models.CharField(max_length=255, null=True, blank=True)
    other_revenue = models.CharField(max_length=255, null=True, blank=True)
    net_revenue = models.CharField(max_length=255, null=True, blank=True)
    rrr = models.CharField(max_length=255, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)


class Result(models.Model):
    """
    A model to represent a result for a search on this file.

    This model also serves to be the primary mapping table between
    files, unit/timestamp groups and searches. Therefore template
    results are created before a result is submitted by the user

    Fields:
        # Mapping fields
        file: a ForeignKey to the file this results was found in
        search: a Foreign key to the search this result refers to
        keyword: a ManyToMany field for all the keywords this result
                 can be associated with
        unit_group: a ForeignKey to the unit_group this result is
                    associated with
        timestamp_group: a ForeignKey to the timestamp_group this result is
                    associated with
        # Result fields
        page: a ForeignKey to the page this result was found on
        submitted_on: a DateTimeField for the datetime this result was
                      submitted
        result: a CharField for the value of this result
        unit: a CharField for the unit that were found for this result
        timestamp: a CharField for the timestamp that was found for
                   this result
        user: A ForeignKey to the Django User that submitted this result

    """

    # The Mapping Columns
    file = models.ForeignKey(File, on_delete=models.CASCADE)

    # search = models.CharField(max_length=140, null=True, blank=True)
    search = models.ForeignKey("StoredSearch", on_delete=models.CASCADE,
                               to_field="description")

    keyword = models.ManyToManyField(Keyword, blank=True,
                                     through="ResultKeyword")
    unit_group = models.ForeignKey("UnitGroup", on_delete=models.CASCADE)
    timestamp_group = models.ForeignKey("TimestampGroup",
                                        on_delete=models.CASCADE)

    # The Result Columns
    page = models.ForeignKey(Page, on_delete=models.CASCADE, null=True,
                             blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,
                             blank=False)
    # page_number = models.CharField(max_length=20, null=True, blank=True)
    submitted_on = models.DateTimeField(blank=True, null=True)
    result = models.CharField(max_length=140, null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)
    timestamp = models.CharField(max_length=20, null=True, blank=True)
    notes = models.CharField(max_length=140, null=True, blank=True)
    uncertainty_flag = models.CharField(max_length=20, default='No')
    version = models.CharField(max_length=20, null=True)
    del_id = models.IntegerField(null=True)
    storedsearch_id = models.IntegerField(null=True)
    searchset_id = models.IntegerField(null=True)
    # sector = models.CharField(max_length=255, blank=True, null=
    auto_added_flag = models.BooleanField(default=False)

    @classmethod
    def create(cls, file, search, unit_group, unit_group_default,
               timestamp_group, timestamp_group_default):
        """
        If this result has not already been created, create this result
        and any related models that were not already created

        Args:
            file: the file this result is for
            search: the search this result is an answer to
            unit_group: the unit group this result belongs to
            unit_group_default: the default value for the unit group
            timestamp_group: the timestamp group this result belongs to
            timestamp_group_default: the default value for the timestamp

        Returns:
            the created result
        """

        # Create the unit group for this result
        model_unit_group, created = UnitGroup.create(
            file=file,
            name=unit_group,
            default_unit=unit_group_default
        )
        # Create the timestamp group for this result
        model_timestamp_group, created = TimestampGroup.create(
            file=file,
            name=timestamp_group,
            default_timestamp=timestamp_group_default
        )
        model_unit_group.save()
        model_timestamp_group.save()

        # Compile a list of all the keywords for this search
        keyword_list = []
        for keyword in search.keywords.all():
            keyword_list.append(keyword)

        # Create the result if it does not already exist
        result, created = cls.objects.get_or_create(
            file=file,
            search=search,
            unit_group=model_unit_group,
            timestamp_group=model_timestamp_group
        )

        # Create any keywords that do not already exist
        for keyword in keyword_list:
            ResultKeyword.objects.get_or_create(keyword=keyword, result=result)
        return result

    def submit(self, value, unit, timestamp, page, user, notes, uncertainty_flag, version, auto_added_flag):
        # , del_id, storedsearch_id, searchset_id
        """
        Submit a value for the result, timestamp and unitgroup
        Args:
            value: the value for this result
            units: the units for this result
            timestamp: the timestamp for this results
            page: the page this result was found on
            user: the current active Django User

        Returns:
            the result after it has been changed

        """

        self.result = value
        self.unit = unit
        self.timestamp = timestamp
        self.page = page
        self.submitted_on = datetime.datetime.now()
        self.user = user
        self.notes = notes
        self.uncertainty_flag = uncertainty_flag
        self.version = version
        self.auto_added_flag = auto_added_flag
        # self.del_id = del_id
        # self.searchset_id = searchset_id
        # self.storedsearch_id = storedsearch_id

        # Adjust the unit and timestamp groups according to the submitted
        # results
        if self.unit and self.unit_group.unit != self.unit:
            unit_group = self.unit_group
            unit_group.unit = self.unit
            unit_group.save()

        if self.timestamp and self.timestamp_group.timestamp != self.timestamp:
            timestamp_group = self.timestamp_group
            timestamp_group.timestamp = self.timestamp
            timestamp_group.save()
        if page:
            page.previous_match = True
            page.save()

        return self

    def clear(self):
        """
        Reset this result back to being a placeholder.

        This is to avoid deleting the mapping when the result is
        deleted, instead, the result is cleared.

        """

        self.result = None
        self.unit = None
        self.timestamp = None
        if len(Result.objects.filter(page=self.page)) == 1:
            self.page.previous_match = False
        if self.page:
            self.page.save()
        self.page = None
        self.submitted_on = None
        self.user = None
        self.notes = None
        self.uncertainty_flag = 'No'
        self.version = None
        # self.del_id = None
        # self.searchset_id = None
        # self.storedsearch_id = None
        self.save()
        if len(Result.objects.filter(unit_group=self.unit_group,
                                     result__isnull=False)) == 0:
            self.unit_group.unit = \
                self.unit_group.default_unit
            self.unit_group.save()

        if len(Result.objects.filter(timestamp_group=self.timestamp_group,
                                     result__isnull=False)) == 0:
            self.timestamp_group.timestamp = \
                self.timestamp_group.default_timestamp
            self.timestamp_group.save()

        self.save()

    def __str__(self):
        return "{0}, {1}: {2}".format(self.file, self.search, self.result)


class ResultKeyword(models.Model):
    """
    A mapping table for the Many to Many field between Result and Keyword

    Fields:
        keyword: a ForeignKey to the keyword being mapped
        result: a ForeignKey to the result being mapped
    """

    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)
    result = models.ForeignKey(Result, on_delete=models.CASCADE)


class SearchSet(models.Model):
    """
    A Model to represent a set of Searches that are applied together

    Fields:
        searches: a ManyToManyField for the searches that belong to this
                  searchset
        file_of_origin: a FilePathField to the location this searchset
                        was loaded in from
    """
    searches = models.ManyToManyField("StoredSearch", blank=True)
    file_of_origin = models.FilePathField(path=PATH_TO_SEARCH_LISTS,
                                          max_length=255)

    @classmethod
    def create(cls, file_of_origin):
        """
        If this searchset does not already exist, create it
        Args:
            file_of_origin: the file that this searchset was
                            created from

        Returns:
            the created search set and a boolean on whether or not it is
            new
        """
        self, created = cls.objects.get_or_create(
            file_of_origin=file_of_origin)
        return self, created


class StoredSearch(models.Model):
    """
    A model to represent a stored search as defined by a search set.

    Fields:
        keywords: A Many to Many field for the keywords that are used in
                  this search
        description: A CharField describing this search in a human
                     friendly way
        search_type: A CharField describing what type of search this is
                     (this is not a relational field to avoid bloat)
        sub_type: A CharField describing the sub type of search type
                  that this search belongs to
    """
    del_id = models.IntegerField(null=True)
    searchset_id = models.IntegerField(null=False, default=0)
    keywords = models.ManyToManyField(Keyword, blank=True)
    description = models.CharField(max_length=140, unique=True)
    search_type = models.CharField(max_length=30)
    sub_type = models.CharField(max_length=30)

    def keyword_list(self):
        """
        Returns:
            A list of keywords that are used in this search
        """
        return [keyword.keyword for keyword in self.keywords.all()]

    @classmethod
    def find_by_keywords(cls, keywords):
        """
        Find a stored search that best matches the keywords given

        Args:
            keywords: the keywords searched for

        Returns: the relevant best matching search

        """
        matching_searches = cls.objects.all()
        for keyword in keywords:
            # print("Key: ", keyword)

            alts = keyword.alt_list()
            new_matching_searches = \
                matching_searches.filter(keywords__in=alts).distinct()
            if len(new_matching_searches) > 0:
                matching_searches = new_matching_searches

            if len(matching_searches) == 1:
                return matching_searches[0]

        best_matching_search = sorted(matching_searches,
                                      key=lambda search:
                                      search.keywords.count())[0]
        # print("matching_searches: ", matching_searches)

        return best_matching_search

    @classmethod
    def create(cls, del_id, keywords, description, search_type, sub_type, searchset_id):
        """
        If this search does not already exist. create it
        Args:
            del_id: the order in which this should be performed
            keywords: the keywords for this search
            description: the human description of this search
            search_type: the type of this search
            sub_type: the sub type of this search

        Returns:
            the created search
        """
        # self, created = cls.objects.get_or_create( del_id=del_id,
        #                                             description=description,
        #                                             search_type=search_type,
        #                                             sub_type=sub_type)
        # m = cls.objects.filter(del_id=del_id,
        #                        description=description,
        #                        search_type=search_type,
        #                        sub_type=sub_type, searchset_id=searchset_id)

        if cls.objects.filter(del_id=del_id,
                              description=description,
                              search_type=search_type,
                              sub_type=sub_type, searchset_id=searchset_id):

            # check if object exist exactly in db
            self = cls.objects.get(del_id=del_id,
                                   description=description,
                                   search_type=search_type,
                                   sub_type=sub_type, searchset_id=searchset_id)
            # print("THIS IS IN THE DB.....")
        else:
            # print("THIS IS NOT IN THE DB")
            if cls.objects.filter(del_id=del_id, searchset_id=searchset_id):
                # if object doesn't exist, check if del_id exist and update other fields if it does
                update_record = cls.objects.get(del_id=del_id)
                update_record.description = description
                update_record.search_type = search_type
                update_record.sub_type = sub_type
                update_record.searchset_id = searchset_id
                update_record.save()
                self = cls.objects.get(del_id=del_id,
                                       description=description,
                                       search_type=search_type,
                                       sub_type=sub_type, searchset_id=searchset_id)
            else:
                # otherwise create the record
                new_record = cls(del_id=del_id,
                                 description=description,
                                 search_type=search_type,
                                 sub_type=sub_type, searchset_id=searchset_id)
                new_record.save()
                self = cls.objects.get(del_id=del_id,
                                       description=description,
                                       search_type=search_type,
                                       sub_type=sub_type, searchset_id=searchset_id)

        for keyword in keywords:
            keyword, created = Keyword.create(keyword)
            self.keywords.add(keyword)
        self.save()
        return self

    def __str__(self):
        return self.description


class UnitGroup(models.Model):
    """
    A model to represent a grouping of searches/results that are
    expected to have the same units (currencies, counts etc.)

    Fields:
        file: a ForeignKey to the file that this unit group belongs to
        name: a CharField to label the unit group
        default_unit: a CharField for the symbol/unit this group
                      defaults to
        unit: a CharField for the current unit that this group is using

    """
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    name = models.CharField(max_length=140)
    default_unit = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)

    @classmethod
    def create(cls, file, name, default_unit):
        """
        If this UnitGroup does not exist, create it
        Args:
            file: the File this unit group belongs to
            name: the label for this group
            default_unit: the default unit for this group

        Returns:
            the created group and a boolean detailing if it was new
        """

        self, created = cls.objects.get_or_create(file=file, name=name,
                                                  default_unit=default_unit)
        self.unit = default_unit
        self.save()
        return self, created

    def __str__(self):
        return "{0}: {1}".format(self.name, self.unit)


class TimestampGroup(models.Model):
    """
        A model to represent a grouping of searches/results that are
        expected to have the same timestamps

        Fields:
            file: a ForeignKey to the file that this unit group belongs to
            name: a CharField to label the unit group
            default_timestamp: a CharField for the symbol/unit this group
                          defaults to
            timestamp: a CharField for the current unit that this group is
            using

        """
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    name = models.CharField(max_length=140)
    timestamp = models.CharField(max_length=255)
    default_timestamp = models.CharField(max_length=255)

    @classmethod
    def create(cls, file, name, default_timestamp):
        """
        If this UnitGroup does not exist, create it
        Args:
            file: the File this unit group belongs to
            name: the label for this group
            default_unit: the default unit for this group

        Returns:
            the created group and a boolean detailing if it was new
        """

        self, created = cls.objects.get_or_create(file=file, name=name,
                                                  default_timestamp=default_timestamp)
        self.timestamp = default_timestamp
        self.save()
        return self, created

    def __str__(self):
        return "{0}: {1}".format(self.name, self.timestamp)


class Country(models.Model):
    """
    A model to represent a set of countries defined by the user custom names.
    The Country name should be added by the users manually
    Fields:
        country_name:
    """
    Country = models.CharField(default='', max_length=100)
    English_short_name = models.CharField(default='', max_length=100)
    Alpha_3_code = models.CharField(default='', max_length=100)
    Time_Entry_System = models.CharField(default='', max_length=100)
    Swift_Charge_Code = models.CharField(default='', max_length=100)
