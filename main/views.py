import re
import os
import time
import logging
import csv
import pandas as pd

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import password_change
from django.forms import formset_factory
from django.http import JsonResponse
from macholib.mach_o import mach_header

from Deloitte_Dynamics.settings import PATH_TO_PDF_FILES, \
    PATH_TO_KEYWORD_FILES, PATH_TO_SEARCH_LISTS, LOG_PATH, PATH_TO_SAP_FILES, PRINT_STATEMENT
from main import models as md
from main.assets.helpers.file_check import check_for_file
from main.assets.helpers import bulk_add_keywords as bulk
from main.assets.helpers import add_sap_data as sap
from main.assets.helpers.database_shortcuts import filter_searches
from main.assets.helpers.query_set_to_list import query_list, query_list_direct
from main.assets.services.managers import generate_searches
from main.assets.services.managers import FileManager, SectionManager
from main.assets.helpers.calculation_parser import calculate_strings
from .forms import FileForm, KeywordForm, ResultForm, AlternativesForm, \
    DescriptionSelectionForm
# from main import main_script
from main.assets.services import all_reports


logger = logging.getLogger(__name__)
_this_dir = os.getcwd()
logging.basicConfig(filename=LOG_PATH,
                    level='INFO')

@login_required()
def dynamics_password_change(request):
    return password_change(request,
                           template_name="registration/password_change.html")


@login_required()
def load(request):
    """
    This page handles the selection of a report and a search set.
    This page is loaded immediately on log in and is the beginning of
    the process.
    """

    logger.info("Loading the load page")
    if 'file' in request.session:
        logger.info("Clearing the session")
        del (request.session['file'])
    if 'searches' in request.session:
        del (request.session['searches'])

    if 'summary_export' in request.POST:
        file_list = list(set(list(md.Result.objects.values_list('file', flat=True))))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="progress_summary.csv"'
        writer = csv.writer(response)
        writer.writerow(['File', 'Completed', 'Missing', 'Skipped', 'Remaining'])

        for file in file_list:
            num_searches = md.Result.objects.filter(file=file, )
            empty_searches, filled_searches, \
            not_found_searches, skipped_searches = filter_searches(file)
            writer.writerow([file, "'{0}/{1}'".format(filled_searches.count(),
                                                   num_searches.count()),
                            "'{0}/{1}'".format(not_found_searches.count(),
                                             num_searches.count()),
                            "'{0}/{1}'".format(skipped_searches.count(),
                                             num_searches.count()),
                            "'{0}/{1}'".format(empty_searches.count(),
                                             num_searches.count()),
                            ])
        return response

    if 'full_export' in request.POST:
        print("inside full_export...")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="full_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['File', 'Search', 'Type', 'Sub-Type', 'Result', 'Units', 'Date', 'Page',
                         'Last edited on', 'Submitted by', 'Version', 'Flagged as uncertain'])

        # sap_data = md.SapData.objects.filter(project=map(find_wbs, file))

        # my_list = []
        c = 1
        # count = md.Result.objects.filter(result__isnull=False).count()
        result_ids_list = md.Result.objects.values_list('storedsearch_id')
        # print('result_ids_list len: ', len(result_ids_list))
        for row in md.Result.objects.filter(result__isnull=False):
            # my_list.append([row.file, row.search, row.search.search_type, row.search.sub_type, row.result, row.unit,
            #  row.timestamp, row.page, row.submitted_on, row.user])
            # get Storedsearch model
            search_type = ''
            sub_type = ''
            search = None
            # added for local try
            try:
                if row.storedsearch_id is not None:
                    std_model = md.StoredSearch.objects.get(id=row.storedsearch_id)

                    search = std_model
                    search_type = std_model.search_type
                    sub_type = std_model.sub_type

            except:
                # print('row.storedsearch_id: ', row.storedsearch_id)
                 pass
            writer.writerow([row.file, search, search_type, sub_type, row.result, row.unit,
                             row.timestamp, row.page, row.submitted_on, row.user, row.version, row.uncertainty_flag])

            c = c + 1
        return response

    if 'full_export_with_sap' in request.POST:
        if md.SapData.objects.all():
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="full_export_with_sap.csv"'

            # process relevant models into one dataframe for exporting
            df_sap = pd.DataFrame(list(md.SapData.objects.all().values()))
            df_result = pd.DataFrame(list(md.Result.objects.all().values()))

            df_sap.drop_duplicates()

            df_sap.rename(columns={'id': 'sap_id'}, inplace=True)
            df_result.rename(columns={'id': 'result_id'}, inplace=True)

            df_result['WBS'] = df_result['file_id'].apply(lambda x: x.replace('_', '-')[:9])

            df = df_result.merge(df_sap, how='left', left_on=['WBS'], right_on=['project'])

            # write result to csv
            writer = csv.writer(response)
            writer.writerow(['result_id', 'submitted_on', 'result', 'unit', 'timestamp', 'file_id', 'page_id', 'search_id',
                             'timestamp_group_id', 'unit_group_id', 'user_id', 'notes', 'uncertainty_flag', 'version', 'sap_id', 'year', 'billing_partner',
                             'master_profit_centre', 'project', 'project_name', 'project_customer_no', 'project_customer',
                             'g_m_uhc', 'cust_industry', 'g_m_pe', 'g_m_uhc_industry', 'g_m_uhc_subindustry', 'sector',
                             'industry', 'customer_type', 'slc_code', 'g_m_uhc_segmt', 'uhc', 'uhc_number', 'gross_revenue',
                             'provisions', 'net_services', 'product_sales', 'other_revenue', 'net_revenue', 'rrr',
                             'file_name'])
            for index, row in df.iterrows():
                writer.writerow([row['result_id'], row['submitted_on'], row['result'], row['unit'], row['timestamp'],
                                row['file_id'], row['page_id'], row['search_id'], row['timestamp_group_id'],
                                row['unit_group_id'], row['user_id'], row['notes'], row['uncertainty_flag'], row['version'], row['sap_id'], row['year'],
                                row['billing_partner'], row['master_profit_centre'], row['project'], row['project_name'],
                                row['project_customer_no'], row['project_customer'], row['g_m_uhc'], row['cust_industry'],
                                row['g_m_pe'], row['g_m_uhc_industry'], row['g_m_uhc_subindustry'], row['sector'],
                                row['industry'], row['customer_type'], row['slc_code'], row['g_m_uhc_segmt'], row['uhc'],
                                row['uhc_number'], row['gross_revenue'], row['provisions'], row['net_services'],
                                row['product_sales'], row['other_revenue'], row['net_revenue'], row['rrr'],
                                row['file_name']])
        else:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="full_export_with_sap.csv"'

            writer = csv.writer(response)
            writer.writerow(['File', 'Search', 'Type', 'Sub-Type', 'Result', 'Units', 'Date', 'Page',
                             'Last edited on', 'Submitted by', 'Dynamics Version', 'Flagged as uncertain', 'SAP Data'])

            for row in md.Result.objects.all():
                writer.writerow(
                    [row.file, row.search, row.search.search_type, row.search.sub_type, row.result, row.unit,
                     row.timestamp, row.page, row.submitted_on, row.user, row.version, row.uncertainty_flag, 'NO SAP DATA FOUND'])

        return response
    # ----------------------------------------------------- #
    if 'all_reports_export' in request.POST:
        print("inside all_reports_export...!")
        keyword_list = request.POST['keyword_tags'].split(',')
        word_lst = [w.lower() for w in keyword_list]
        # search_res = main_script.search_index(['cost', 'IT', 'separation'], index_name='dynamic_pdfs', pages=None)
        search_res = all_reports.search_index(word_lst, index_name='test_dynamic', pages=None)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_reports_export.csv"'

        # writer = csv.writer(response)
        csv_out = csv.writer(response)
        csv_out.writerow(['Score', 'Page No.', 'Page Text', 'File Name'] + [w + " count" for w in word_lst] +
                         ["Keywords"] + [w + " file_count" for w in word_lst])

        main_list = []
        file_count_dict = dict()
        for row in search_res[1]:
            page_txt_lst = row[3].replace("\n", '').lower().split()
            wordfreq = [page_txt_lst.count(w.lower()) for w in word_lst]
            count_lst = list(zip(word_lst, wordfreq))

            # csv_out.writerow((row[0], row[1], row[3].replace("\n", '').strip(), row[4]))
            row_col_lst = [row[0], row[1], row[3].replace("\n", '').strip(), row[4].split('\\')[-1]]  # + count_lst
            word_appear = []
            for cw in count_lst:
                row_col_lst.append(str(cw[1]))
                if cw[1] != 0:
                    word_appear.append(cw[0])

            # add file count
            filename = row_col_lst[3]
            if filename not in file_count_dict.keys():
                f_c_dict = dict()
                for c, count_data in enumerate(count_lst):
                    f_c_dict[count_data[0]] = count_data[1]

                # file_count_dict[filename] = {count_lst[0][0]: count_lst[0][1],
                #                              count_lst[1][0]: count_lst[1][1],
                #                              count_lst[2][0]: count_lst[2][1],
                #                              # count_lst[3][0]: count_lst[3][1],
                #                              }
                file_count_dict[filename] = f_c_dict
            else:
                f_c_dict = dict()
                for c, count_data in enumerate(count_lst):
                    f_c_dict[count_data[0]] = count_data[1] + file_count_dict[filename][count_lst[c][0]]
                # file_count_dict[filename] = {
                #     count_lst[0][0]: count_lst[0][1] + file_count_dict[filename][count_lst[0][0]],
                #     count_lst[1][0]: count_lst[1][1] + file_count_dict[filename][count_lst[1][0]],
                #     count_lst[2][0]: count_lst[2][1] + file_count_dict[filename][count_lst[2][0]],
                #     # count_lst[3][0]: count_lst[3][1] + file_count_dict[filename][count_lst[3][0]],
                #
                #     }
                file_count_dict[filename] = f_c_dict
            # csv_out.writerow(row_col_lst)
            s = '|'.join(word_appear)
            row_col_lst.append(s)
            main_list.append(row_col_lst)
        # pprint(file_count_dict)
        for row_lst in main_list:
            file_name = row_lst[3]
            for fw in word_lst:
                row_lst.append(file_count_dict[file_name][fw])
            csv_out.writerow(row_lst)

        return response

    # ----------------------------------------------------- #
    # Check country in path :
    cnt_dir = [x for x in os.walk(PATH_TO_PDF_FILES)]
    cnt_dir = cnt_dir[0][1]
    opration_country_object = md.Country.objects.all()
    for cnt_obj in opration_country_object:
        if cnt_obj.Alpha_3_code not in cnt_dir:
            print("True-----------------------")
            # Directory
            directory = cnt_obj.Alpha_3_code
            # Parent Directory path
            parent_dir = PATH_TO_PDF_FILES
            # Path to create
            path_to_create = os.path.join(parent_dir, directory)
            # Create the directory
            os.mkdir(path_to_create)
            print("Directory '% s' created" % directory)
    template = "main/load.html"
    context = {'file_form': FileForm(PATH_TO_PDF_FILES, "pdf"),
               'search_file_form': FileForm(PATH_TO_SEARCH_LISTS, "xlsx", prefix="search",
                                            check_box='Reset'),
               'country_form': FileForm(PATH_TO_SEARCH_LISTS, "xlsx", country_form=True),
               'page': "load", 'session': request.session.get_expiry_age()}  # the form to pick the searchset

    return render(request, template, context)


@login_required()
def keyword_upload(request):
    """
    This page displays inputs that can be used to add keywords to the
    database. It also has an expandable list of the existing keyword
    relationships.
    """

    logger.info("Loading the keyword page")
    template = "main/alt.html"

    alt_form_set = formset_factory(AlternativesForm,
                                   extra=6)  # formset factory is a django method to repeat forms
    file_form = FileForm(PATH_TO_KEYWORD_FILES, "xlsx")
    context = {'alt_form_set': alt_form_set,
               # alt form is the input for uploading an alternative keywords
               'file_form': file_form}

    if 'file' in request.POST and request.POST['file'].endswith('.xlsx'):
        file = request.POST['file']
        bulk.excel_import(file)  # this bulk imports alternative keywords from
        # an excel file
        context['uploaded'] = True
        file_form.initial = {'file': file}
        context['file_form'] = file_form

    # this takes any submitted alternative keywords, and uploads them to the database
    if re.search(r'form-\d-alternative_keyword', str(request.POST.keys())):
        alt_keys = []
        for key, value in request.POST.items():
            if re.match(r'form-\d-alternative_keyword', key):
                if len(value) > 0:
                    alt_keys.append(value)
        bulk.list_upload(alt_keys)

    with connection.cursor() as cursor:
        cursor.execute("""
        SELECT	DISTINCT from_keyword_id + ', ' + STUFF ((SELECT  ', '+ to_keyword_id + ''
                                                          FROM  (
                                                            SELECT DISTINCT from_keyword_id, to_keyword_id
                                                            FROM	main_keyword_alternatives)	T
                                                                WHERE  T.from_keyword_id = Q.from_keyword_id
                                                                ORDER BY to_keyword_id
                                                                FOR XML PATH(''),TYPE).value('(./text())[1]','NVARCHAR(MAX)'), 1, 2 ,''
                                                                )	KEYWORD_ALTERNATIVES
                                                          FROM main_keyword_alternatives  Q
                                                          """
                       )

        keywords = ["".join(i).split(",") for i in cursor.fetchall()]
        keywords = [[x.strip() for x in i] for i in keywords]

        added = []
        keywords_list = []
        if keywords:
            longest_sublist = max([len(sublist) for sublist in keywords])
            for keyword_set in keywords:
                new_keyword_set = []
                for i in range(longest_sublist):
                    if i < len(keyword_set):
                        if keyword_set[i] not in added:
                            new_keyword_set.append(keyword_set[i])
                            added.append(keyword_set[i])
                    elif len(new_keyword_set) > 0:
                        new_keyword_set.append("")
                keywords_list.append(new_keyword_set)
    if 'delete' and 'keywords_to_change' in request.POST:
        keywords_to_change = request.POST.getlist('keywords_to_change')
        model_keywords = md.Keyword.objects.filter(
            keyword__in=keywords_to_change)
        for model_keyword in model_keywords:
            model_keyword.delete()
            model_keyword.save()
        return HttpResponseRedirect('/alt_keys')

    context['page'] = "alts"
    context['synonyms'] = keywords_list
    return render(request, template, context)

@login_required()
def sap_integration(request):
    """
    This page to upload a sap extract for
    :param request:
    :return:
    """

    # TODO: ADD FILE AS FIELD IN MODEL AND LIST OF LOADED IN FILES INTO FRONT END

    logger.info("Loading the sap upload page")
    template = 'main/sap.html'
    sap_file_form = FileForm(PATH_TO_SAP_FILES, "xlsx")
    context = {'sap_file_form': sap_file_form
               }
    context['sap'] = md.SapData.objects.values('file_name').distinct()

    if 'file' in request.POST and request.POST['file'].endswith('.xlsx'):
        file_name = request.POST['file']
        file_name_list = str(file_name).rsplit('\\', 1)
        if file_name_list[1] not in md.SapData.objects.values_list('file_name', flat=True).distinct():
            file = request.POST['file']
            sap_dict = sap.sap_excel_import(file)  # this bulk imports alternative keywords from
            model_instances = [md.SapData(
                year=record['year'],
                billing_partner=record['billing_partner'],
                master_profit_centre=record['master_profit_centre'],
                project=record['project'],
                project_name=record['project_name'],
                project_customer_no=record['project_customer_no'],
                project_customer=record['project_customer'],
                g_m_uhc=record['g_m_uhc'],
                cust_industry=record['cust_industry'],
                g_m_pe=record['g_m_pe'],
                g_m_uhc_industry=record['g_m_uhc_industry'],
                g_m_uhc_subindustry=record['g_m_uhc_subindustry'],
                sector=record['sector'],
                industry=record['industry'],
                customer_type=record['customer_type'],
                slc_code=record['slc_code'],
                g_m_uhc_segmt=record['g_m_uhc_segmt'],
                uhc=record['uhc'],
                uhc_number=record['uhc_number'],
                gross_revenue=record['gross_revenue'],
                provisions=record['provisions'],
                net_services=record['net_services'],
                product_sales=record['product_sales'],
                other_revenue=record['other_revenue'],
                net_revenue=record['net_revenue'],
                rrr=record['rrr'],
                file_name=record['file_name']) for record in sap_dict]
            md.SapData.objects.bulk_create(model_instances)
        else:
            context['upload_flag'] = True

    if 'delete_sap' in request.POST:
        logger.info("Deleted all the results")
        file_name = request.POST['delete_sap']
        for model_result in md.SapData.objects.filter(
                file_name=file_name
        ):
            model_result.delete()

    return render(request, template, context)


@login_required()
def contents(request):
    """
    On page load this page takes a selected report and search set and
    generated the searches for this match. The file is processed and
    indexed and the digital contents page is displayed in page.
    """
    try:
        print('Insde try........!')
        logger.info("Loading the contents page")

        template = "main/contents.html"

        # check for file looks for a file in the HTTP request
        # and returns it if # found, or redirects to the load page
        file_path = check_for_file(request)
        print("file_path: ", file_path)
        if not file_path:
            logger.error("No file was found")
            return HttpResponseRedirect("/load")

        # initiate a FileManager to handle this file
        file = FileManager(file_path)
        if 'file' not in request.session:
            file.process_file()
            file.write_to_file()
            file.store_pages()

        # this stores the file name as a variable for the duration of the
        # session of the user
        request.session['file'] = file.name
        request.session['file_contents'] = file.contents

        if 'check' in request.GET:
            md.Result.objects.filter(file=file.model_file).delete()

        if 'search_file' in request.GET:
            search_file = (request.GET['search_file'])
            searches = generate_searches(search_file, file.model_file)
            request.session['search_set_id'] = searches.id

        context = {"file_name": file.name, "url": "Contents",
                   "page": str(file.model_file.name)}

        section_zip = file.model_file.find_sub_sections()  # finds all the
        file_obj = md.File.objects.get(name=file.name)
        # subsections in the file
        context['file'] = file.model_file
        context['section_zip'] = section_zip
        context['keyword_form'] = KeywordForm
        context['page'] = "scan"
        context['cmp_description'] = file_obj.company_description
        country_obj = md.Country.objects.get(Alpha_3_code=file_obj.source_country)
        country_name = str(country_obj.Country + "-" + country_obj.Alpha_3_code)
        context['member_firm'] = country_name  # file_obj.source_country

        opration_country_object = md.Country.objects.all()
        context['all_member_firm'] = opration_country_object
        context['file_path'] = file_obj.name

        return render(request, template, context)
    except Exception as e:
        print('inside error......!')
        print(e)
        raise e
    print('after try except...!')
    # return render(request, template, context)

    
# Checking number is float or not
def is_float(n):
  try:
    float_n = float(n)
  except ValueError:
    return int(n)#False
  else:
    return float(n) #True


@login_required()
def stored_searches(request):
    """
    This page displays the results of a search, it allowed for
    submission of a result or for changing the page in view.
    It displays the PDF in view and has raw text beneath.
    """

    logger.info("Loading the report page")

    file_contents = request.session['file_contents']
    sections_to_search = None
    page_object = None
    template = "main/report.html"
    context = {}
    file = check_for_file(request)
    if not file:
        logger.error("No file was found")
        return HttpResponseRedirect("/load")

    if 'search_set_id' in request.session:
        try:
            search_set = md.SearchSet.objects.get(
                id=request.session['search_set_id'])
        except md.SearchSet.DoesNotExist:
            return HttpResponseRedirect("/load")

    else:
        return HttpResponseRedirect("/load")

    model_file = md.File.objects.get(name=file)
    model_search = None
    free_search = None
    model_keywords = None

    empty_searches, filled_searches, \
    not_found_searches, skipped_searches = filter_searches(model_file, search_set.id)

    # get empty searches and relevant id
    # submit the results of the previous search if there was a previous search
    if 'result' and 'completed_search' in request.POST:
        logger.info("A result was submitted")
        # Create dictionary for combine result auto a
        completed_search_dict = {
            "Value of synergies from IT (combined capex and opex)":
                ["Value of synergies from IT function (capex)", "Value of synergies from IT function (opex)"],
            "Value of synergies from IT function (capex)": {
                "Combined": "Value of synergies from IT (combined capex and opex)",
                "SubValue": "Value of synergies from IT function (opex)"
            },
            "Value of synergies from IT function (opex)": {
                "Combined": "Value of synergies from IT (combined capex and opex)",
                "SubValue": "Value of synergies from IT function (capex)"
            },
            "Value of synergies from R&D (capex)": {
                "Combined": "Value of synergies from R&D (combined capex and opex)",
                "SubValue": "Value of synergies from R&D (opex) function"},
            "Value of synergies from R&D (opex) function": {
                "Combined": "Value of synergies from R&D (combined capex and opex)",
                "SubValue": "Value of synergies from R&D (capex)"
            },

        }
        # checking values for combine entry
        selected_val = request.POST['completed_search']
        result_search_combine = None
        model_result_subvalue = None
        if selected_val in completed_search_dict.keys():
            combined_obj = md.Result.objects.get(file_id=model_file,
                                                 search_id=completed_search_dict[selected_val]['Combined'])
            subvalue_obj = md.Result.objects.get(file_id=model_file,
                                                 search_id=completed_search_dict[selected_val]['SubValue'])

            logger.info("subValue_obj.user_id")
            logger.info(subvalue_obj.user_id)
            logger.info("combined_obj.user_id")
            logger.info(combined_obj.user_id)
            logger.info(type(combined_obj.user_id))

            if subvalue_obj.user_id and combined_obj.user_id == None:
                logger.info("Need to store subvalue object also ..........................")
                result_search_combine = md.StoredSearch.objects.get(
                    description=completed_search_dict[selected_val]['Combined'], searchset_id=search_set.id)
                model_result_subvalue = result_search_combine.result_set.get(file=model_file)
        logger.info(request.POST['completed_search'])

        # Now the main process starts
        result_search = md.StoredSearch.objects.get(
            description=request.POST['completed_search'], searchset_id=search_set.id)
        model_result = result_search.result_set.get(file=model_file)
        try:
            page = md.Page.objects.get(file=model_file,
                                   page_number=request.POST[
                                       'page_of_result'])
        except:
            page = md.Page.objects.filter(file=model_file)[0]

        result = request.POST['result']

        if result != "TBC" and len(result) != 0:
            result = calculate_strings(result)
        model_result.submit(value=result,
                            unit=request.POST['unit'],
                            timestamp=request.POST['timestamp'],
                            page=page,
                            user=request.user,
                            notes=request.POST['notes'],
                            # new_flag=request.POST.get('new_flag', 0),
                            auto_added_flag=False,
                            uncertainty_flag=request.POST.get('uncertainty_flag', 'No'),
                            version='1.1')
        model_result.save()
        # model_search = result_search
        # Save the combine value object
        if model_result_subvalue is not None:
            subvalue_result = is_float(subvalue_obj.result)
            combin_result = result + subvalue_result

            model_result_subvalue.submit(value=combin_result,
                                unit=request.POST['unit'],
                                timestamp=request.POST['timestamp'],
                                page=page,
                                user=request.user,
                                notes="Added Automatically",
                                auto_added_flag=True,
                                uncertainty_flag=request.POST.get('uncertainty_flag', 'No'),
                                version='1.1')
            model_result_subvalue.save()


        if 'active_search' in request.session:
            logger.info("Searching from active search")
            model_search_id = request.session['active_search'] + 1

            while not model_search and \
                    model_search_id < search_set.searches.count():
                next_search = md.StoredSearch.objects.get(
                    id=model_search_id
                )
                if next_search in (empty_searches or
                                   skipped_searches):
                    model_search = next_search
                else:
                    model_search_id += 1
            if 'sections' in request.session:
                sections_to_search = request.session['sections']

    # if this was selected from the search selector drop down
    elif 'search' in request.GET:
        # model_search = md.StoredSearch.objects.get(description=request.GET[
        #     'search'], searchset_id=search_set.id)
        model_complete_result = md.Result.objects.filter(file_id=request.session['file'],
                                                         search_id=request.GET['search'], searchset_id=search_set.id)
        if len(model_complete_result) > 0:
            model_search = md.StoredSearch.objects.get(id=model_complete_result[0].storedsearch_id)
            page_object = model_complete_result[0].page
        else:
            model_search = md.StoredSearch.objects.get(description=request.GET['search'], searchset_id=search_set.id)

        if 'sections' in request.session:
            sections_to_search = request.session['sections']

    # if this request is using an existing result
    # (user editing existing result)
    elif 'result_id' in request.GET:
        logger.info("Searching from result")
        result_id = request.GET['result_id']
        model_result = md.Result.objects.get(id=result_id)
        # ----- change --------- #
        std_model = md.StoredSearch.objects.get(id=model_result.storedsearch_id)
        model_result.search = std_model
        # ----- change end--------- #
        model_search = model_result.search

    # if this request is using a specific model search ID
    # (user selecting alternate pages)
    elif 'model_search_id' in request.GET:
        logger.info("Searching from given search")
        model_search = md.StoredSearch.objects.get(description=request.GET['model_search_id'],
                                                   searchset_id=request.session['search_set_id'])
        if 'sections' in request.session:
            sections_to_search = request.session['sections']

    # if this request is using keywords to find a search (user inputted search)
    elif 'keywords' in request.GET and 'completed_search' not in request.POST:
        if 'free_search' in request.GET:
            logger.info("Searching from free keywords")
            free_search = [keyword.lower().strip() for keyword in request.GET[
                'keywords'].split(",")]
        else:
            logger.info("Searching model from keywords")
            keywords = [keyword.lower().strip() for keyword in request.GET[
                'keywords'].split(",")]
            model_keywords = [keyword for keyword in
                              md.Keyword.objects.filter(keyword__in=keywords)]
            model_search = md.StoredSearch.find_by_keywords(model_keywords)

    if 'sections' in request.GET:
        logger.info("Searching only in given sections")
        section_manager = SectionManager(request.GET['sections'])
        sections_to_search = section_manager.get_section_names()
        request.session['sections'] = sections_to_search
    if not sections_to_search:
        sections_to_search = None
        # sections_to_search = ['business overview']

    # if this search is using a search set (cycling search) and if there
    # are searches yet to do for this file

    keywords = []
    if not model_search:
        if free_search:
            logger.info("Search from free search")
            keywords = free_search
            model_keywords = [md.Keyword.create(keyword)[0]
                              for keyword in free_search]
            [keyword.save() for keyword in model_keywords]

        elif len(
                md.Result.objects.filter(
                    file=model_file,
                    search__in=search_set.searches.all(),
                    result__isnull=True)) > 0:
            # --- change ---- #
            result_mdl = md.Result.objects.filter(
                file=model_file,
                search__in=search_set.searches.all(),
                result__isnull=True)
            # --- end change ---- #
            # use the next search from the set of searches
            # model_search = md.Result.objects.filter(file=model_file, search=str(query_list(empty_searches)[0]['description']))[0].search

            # model_search_md = md.StoredSearch.objects.filter(description=str(query_list(empty_searches)[0]['description']), searchset_id=search_set.id)
            model_search_md = md.StoredSearch.objects.filter(description=result_mdl[0].search_id, searchset_id=search_set.id)

            if len(model_search_md) > 0:
                model_search = model_search_md[0]

            logger.info("Moved on to the next search")
        else:
            logger.info("There were no remaining searches")
            return HttpResponseRedirect("/results")

    # if a search was selected from the search set
    if model_search:
        request.session['active_search'] = model_search.id
        result = None
        unit = None
        timestamp = None
        # get the result for this search and file
        model_result = md.Result.objects.get(search=model_search,
                                             file=model_file)
        # print("length pf model_result: ", model_result)
        # if there is a pre-existing search populate the fields
        if model_result.result:

            result = model_result.result
            unit = model_result.unit
            timestamp = model_result.timestamp
        # otherwise, populate unit and timestamp with their defaults
        elif model_result.unit_group.unit \
                or model_result.timestamp_group.timestamp:
            if model_result.unit_group.unit:
                unit = model_result.unit_group.unit
            if model_result.timestamp_group.timestamp:
                timestamp = model_result.timestamp_group.timestamp

        # pass the compiled result form into the template
        context['result_form'] = ResultForm(initial={
            'result': result,
            "unit": unit,
            'timestamp': timestamp
        })

        keywords_id = [keyword.keyword for keyword in md.Keyword.objects.filter(storedsearch=model_search)]
        # separate the keywords into individual words
        keywords = [keyword.keyword for keyword in md.Keyword.objects.filter(storedsearch=model_search)]

        if PRINT_STATEMENT:
            print("keyword: ", keywords)
        # collect the models related to those keywords
        model_keywords = [keyword for keyword in md.Keyword.objects.filter(keyword__in=keywords)]

    # before finding the correct pages, default to the first page
    page_to_view = md.Page.objects.filter(file=model_file, page_number=0)
    sorted_pages = [page_to_view, ]
    # if a search of some sort has been compiled
    if model_keywords:
        if PRINT_STATEMENT:
            print("sections_to_search: "), sections_to_search
        # attempt to execute the search
        try:
            start_sort = time.time()
            # file manager handles the file
            file_manager = FileManager(file)
            # search index searches the corresponding index with the
            # compiled search
            search_res = file_manager.search_index(model_keywords,
                                                   sections_to_search)
            # if the search failed and had no results

            # if not search_res:
            #     logger.info("The search failed")
            #     if model_search:
            #         # set the result for this search to not found
            #         result = model_search.result_set.get(file=model_file)
            #         value = "No Result found"
            #         # submit this result as not found
            #         result.submit(value, None, None, None, user=request.user, notes=None,
            #         uncertainty_flag='No', version=None)
            #         result.save()
            #     section_zip = model_file.find_sub_sections()
            #     context['file'] = model_file
            #     context['section_zip'] = section_zip
            #     context['keyword_form'] = KeywordForm
            #     context['page'] = "scan"
            #     if model_search:
            #         context['search_failed'] = model_search
            #     else:
            #         context['search_failed'] = ", ".join(keywords)
            #     return render(request, "main/contents.html", context)

            # new function for failed search
            if not search_res:
                logger.info("The search failed")
                context['search_failed'] = model_search
                # model_search = md.StoredSearch.objects.filter(searchset_id=search_set.id)[0]
                # if 'selected_drp' in request.GET:
                #     model_search = md.StoredSearch.objects.get(description=request.GET['selected_drp'],
                #                                                searchset_id=search_set.id)
                # else:
                #     model_search = md.StoredSearch.objects.filter(searchset_id=search_set.id)[0]
                keywords = [keyword.keyword for keyword in md.Keyword.objects.filter(storedsearch=model_search)]
                model_keywords = [keyword for keyword in md.Keyword.objects.filter(keyword__in=keywords)]
                search_res = file_manager.search_index(model_keywords, sections_to_search)

            # the results of this search are the page to view and a list of
            # the pages that hit, sorted by score
            if search_res:
                page_to_view, sorted_pages, = \
                    search_res[0], search_res[1]

            # if a specific page has been specified, overwrite the page to view
            if 'page_selected' in request.GET:
                page_number = int(request.GET['page_selected'])
                for page in sorted_pages:
                    if page.page_number == page_number:
                        page_to_view = page
                        break

            end_sort = time.time()
            logger.info("sorting took {}".format(end_sort - start_sort))

        # if elasticsearch is not running, redirect to load
        except ConnectionRefusedError:
            logger.error("elasticsearch is not running")
            return HttpResponseRedirect("/load")

        # if this was a search from the search set
        if model_search:
            # render the submission pane and pass in the relevant search
            # from the search set
            if 'result_form' not in context:
                context['result_form'] = ResultForm()
            context['model_search'] = model_search

        # render the selection pane for stored searches
        if model_search:
            initial = {'search': model_search.description}
        else:
            search = md.StoredSearch.objects.filter(searchset=search_set)[0]
            initial = {'search': search}

        # context['search_selector'] = DescriptionSelectionForm(
        #     initial=initial,
        #     empty=query_list(empty_searches),
        #     filled=query_list(filled_searches),
        #     not_found=query_list(not_found_searches),
        #     skipped=query_list(skipped_searches)
        # )
        context['search_selector'] = DescriptionSelectionForm(
            initial=initial,
            empty=query_list_direct(empty_searches, search_set.id),
            filled=query_list_direct(filled_searches, search_set.id),
            not_found=query_list_direct(not_found_searches, search_set.id),
            skipped=query_list_direct(skipped_searches, search_set.id)
        )

    if not keywords:
        return HttpResponseRedirect("/results")

    context['keyword_form'] = KeywordForm(initial={
        'keywords': ", ".join(keywords)
    })

    keyword_strings = []
    for model_keyword in model_keywords:
        keyword_strings.append(model_keyword.alt_list(string=True))

    # if keywords not found on page
    if 'page' in request.GET or not search_res or page_object:
        flag = False
        if 'page' not in request.GET and not search_res:
            page_number = int(1)
        elif page_object:
            page_number = page_object.page_number
        else:
            page_number = int(request.GET['page'])
        # page_number = int(request.GET['page'])
        if sorted_pages:
            try:
                for page in sorted_pages:
                    if page.page_number == page_number:
                        page_to_view = page
                        flag = True
                        break
            except:
                print("inside except.................")

        # for page in sorted_pages:
        #     if page.page_number == page_number:
        #         page_to_view = page
        #         flag = True
        #         break
        if flag is False:
            page_link = md.Page.objects.get(file_id=file, page_number=page_number)
            md_section = md.Section.objects.filter(file_id=request.session['file'], first_page__lte=int(page_number),
                                                   last_page__gte=int(page_number))
            search_seaction = [str(md_section[0].name)]
            search_page = file_manager.search_index(model_keywords, search_seaction)
            # pages_stored = search_page[1]
            page_text = "False"
            if search_page:
                pages_stored = search_page[1]
                for page in pages_stored:
                    if page.page_number == page_number:
                        view_page = page
                        page_text = view_page.text.split("\n\n\n")
                        break
            if page_text == 'False':
                # Get page content
                file_contents = request.session['file_contents']
                print("file_contents--: ", file_contents)
                page_content = file_contents[search_seaction[0]][str(page_number)]
                if page_content:
                    page_text = page_content

            context['page_not_found'] = {"link": page_link.link,
                                         "page_txt": page_text,
                                         "page_number": page_number,
                                         }
    file_obj = md.File.objects.get(name=file)
    # Context variable
    context['model_file'] = model_file
    context['page_to_view'] = page_to_view  # page to view is a model page
    if search_res:
        context['page_text'] = page_to_view.text.split("\n\n\n")
        context['results'] = sorted_pages
    # context['page_text'] = page_to_view.text.split("\n\n\n")
    context['keywords'] = keyword_strings
    # context['results'] = sorted_pages
    context['page'] = "scan"
    context['last_page'] = file_obj.num_pages

    return render(request, template, context)


@login_required()
def results(request):
    """
    This page displays any already submitted, skipped or not found
    results. It shows a progress bar up the top and shows the
    submitted results down below. These can be filtered using the drop
    downs in the middle left of the page. These results can be edited
    or deleted. Progress reports or full breakdown of results can also
    be exported to csv.
    """

    logger.info("Loading the review page")
    file = check_for_file(request)
    if not file:
        logger.error("No file was found")
        return HttpResponseRedirect("/load")

    if 'delete' and 'result_id' in request.POST:
        logger.info("Deleted a result")
        result_id = request.POST['result_id']
        model_result = md.Result.objects.get(id=result_id)
        model_result.clear()

    if 'delete_all' in request.POST:
        logger.info("Deleted all the results")
        for model_result in md.Result.objects.filter(
                file=request.session['file'],
                result__isnull=False,
        ):
            model_result.clear()

    # if 'delete_selected' and 'results_to_delete' in request.POST:
    #     logger.info("Deleted all the selected results")
    #     results_to_delete = request.POST.getlist('results_to_delete')
    #     model_results = md.Result.objects.filter(id__in=results_to_delete)
    #     print('START MODEL RESULTS')
    #     print(model_results)
    #     for item in model_results:
    #         print(item)
    #         item.clear()
    #         item.save()
    #     return HttpResponseRedirect('/results')

    if 'summary_export' in request.POST:
        file_list = list(set(list(md.Result.objects.values_list('file', flat=True))))
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="progress_summary.csv"'
        writer = csv.writer(response)
        writer.writerow(['File', 'Completed', 'Missing', 'Skipped', 'Remaining'])
        # # not_found_searches, skipped_searches = filter_searches(model_file, request.session['search_set_id'])
        for file in file_list:
            num_searches = md.Result.objects.filter(file=file, )
            empty_searches, filled_searches, \
            not_found_searches, skipped_searches = filter_searches(file)
            writer.writerow([file, "'{0}/{1}'".format(filled_searches.count(),
                                                   num_searches.count()),
                            "'{0}/{1}'".format(not_found_searches.count(),
                                             num_searches.count()),
                            "'{0}/{1}'".format(skipped_searches.count(),
                                             num_searches.count()),
                            "'{0}/{1}'".format(empty_searches.count(),
                                             num_searches.count()),
                            ])

        return response

    if 'full_export' in request.POST:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="full_export.csv"'

        writer = csv.writer(response)
        writer.writerow(['File', 'Search', 'Type', 'Sub-Type', 'Result', 'Units', 'Date', 'Page',
                         'Last edited on', 'Submitted by', 'Version', 'Flagged as uncertain'])

        # sap_data = md.SapData.objects.filter(project=map(find_wbs, file))

        # my_list = []
        for row in md.Result.objects.all():
            # my_list.append([row.file, row.search, row.search.search_type, row.search.sub_type, row.result, row.unit,
            #  row.timestamp, row.page, row.submitted_on, row.user])
            # writer.writerow([row.file, row.search, row.search.search_type, row.search.sub_type, row.result, row.unit,
            #                  row.timestamp, row.page, row.submitted_on, row.user, row.version, row.uncertainty_flag])
            search_type = ''
            sub_type = ''
            search = None
            if row.storedsearch_id is not None:
                std_model = md.StoredSearch.objects.get(id=row.storedsearch_id)
                search = std_model
                search_type = std_model.search_type
                sub_type = std_model.sub_type

            writer.writerow([row.file, search, search_type, sub_type, row.result, row.unit,
                             row.timestamp, row.page, row.submitted_on, row.user, row.version, row.uncertainty_flag])

        return response

    if 'full_export_with_sap' in request.POST:
        if md.SapData.objects.all():
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="full_export_with_sap.csv"'

            # process relevant models into one dataframe for exporting
            df_sap = pd.DataFrame(list(md.SapData.objects.all().values()))
            df_result = pd.DataFrame(list(md.Result.objects.all().values()))

            df_sap.drop_duplicates()

            df_sap.rename(columns={'id': 'sap_id'}, inplace=True)
            df_result.rename(columns={'id': 'result_id'}, inplace=True)

            df_result['WBS'] = df_result['file_id'].apply(lambda x: x.replace('_', '-')[:9])

            df = df_result.merge(df_sap, how='left', left_on=['WBS'], right_on=['project'])

            # write result to csv
            writer = csv.writer(response)
            writer.writerow(['result_id', 'submitted_on', 'result', 'unit', 'timestamp', 'file_id', 'page_id', 'search_id',
                             'timestamp_group_id', 'unit_group_id', 'user_id', 'notes', 'uncertainty_flag', 'version', 'sap_id', 'year', 'billing_partner',
                             'master_profit_centre', 'project', 'project_name', 'project_customer_no', 'project_customer',
                             'g_m_uhc', 'cust_industry', 'g_m_pe', 'g_m_uhc_industry', 'g_m_uhc_subindustry', 'sector',
                             'industry', 'customer_type', 'slc_code', 'g_m_uhc_segmt', 'uhc', 'uhc_number', 'gross_revenue',
                             'provisions', 'net_services', 'product_sales', 'other_revenue', 'net_revenue', 'rrr',
                             'file_name'])
            for index, row in df.iterrows():
                writer.writerow([row['result_id'], row['submitted_on'], row['result'], row['unit'], row['timestamp'],
                                row['file_id'], row['page_id'], row['search_id'], row['timestamp_group_id'],
                                row['unit_group_id'], row['user_id'], row['notes'], row['uncertainty_flag'], row['version'], row['sap_id'], row['year'],
                                row['billing_partner'], row['master_profit_centre'], row['project'], row['project_name'],
                                row['project_customer_no'], row['project_customer'], row['g_m_uhc'], row['cust_industry'],
                                row['g_m_pe'], row['g_m_uhc_industry'], row['g_m_uhc_subindustry'], row['sector'],
                                row['industry'], row['customer_type'], row['slc_code'], row['g_m_uhc_segmt'], row['uhc'],
                                row['uhc_number'], row['gross_revenue'], row['provisions'], row['net_services'],
                                row['product_sales'], row['other_revenue'], row['net_revenue'], row['rrr'],
                                row['file_name']])
        else:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="full_export_with_sap.csv"'

            writer = csv.writer(response)
            writer.writerow(['File', 'Search', 'Type', 'Sub-Type', 'Result', 'Units', 'Date', 'Page',
                             'Last edited on', 'Submitted by', 'Dynamics Version', 'Flagged as uncertain', 'SAP Data'])

            for row in md.Result.objects.all():
                search_type = ''
                sub_type = ''
                search = None
                if row.storedsearch_id is not None:
                    std_model = md.StoredSearch.objects.get(id=row.storedsearch_id)
                    search = std_model
                    search_type = std_model.search_type
                    sub_type = std_model.sub_type

                writer.writerow(
                    [row.file, search, search_type, sub_type, row.result, row.unit,
                     row.timestamp, row.page, row.submitted_on, row.user, row.version, row.uncertainty_flag, 'NO SAP DATA FOUND'])

        return response
    # Eport all reports data in csv file
    if 'all_reports_export' in request.POST:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_reports_export.csv"'
        # start_1 = time.time()
        word_lst = ['Cost', 'IT', 'Separation']
        # search_res = search_index(['cost', 'IT', 'separation'], index_name='dynamic_pdfs', pages=None)
        search_res = all_reports.search_index(['cost', 'IT', 'separation'], index_name='dynamics', pages=None)
        print("Writing data into csv file")
        # with open('test_count_words_07_2020.csv', 'w', encoding="utf8", newline='') as out:
        csv_out = csv.writer(response)
        csv_out.writerow(['Score', 'Page No.', 'Page Text', 'File Name'] + [w + " count" for w in word_lst] +
                         ["Keywords"] + [w + " file_count" for w in word_lst])
        # cccc
        main_list = []
        file_count_dict = dict()
        for row in search_res[1]:
            page_txt_lst = row[3].replace("\n", '').lower().split()
            wordfreq = [page_txt_lst.count(w.lower()) for w in word_lst]
            count_lst = list(zip(word_lst, wordfreq))

            # csv_out.writerow((row[0], row[1], row[3].replace("\n", '').strip(), row[4]))
            row_col_lst = [row[0], row[1], row[3].replace("\n", '').strip(), row[4].split('\\')[-1]]  # + count_lst
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
                file_count_dict[filename] = {
                    count_lst[0][0]: count_lst[0][1] + file_count_dict[filename][count_lst[0][0]],
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
        return response

        # end_1 = time.time()
        # print("Total time of run 1: ", end_1 - start_1)
        print("Process completed....!")

    # ------------- end ---------------------------------- #
    template = "main/results.html"

    context = {'keyword_form': KeywordForm,
               'url': "Review"}

    file_name = request.session['file']

    model_file = md.File.objects.get(name=file_name)

    context['file'] = model_file

    num_searches = md.Result.objects.filter(
        file=model_file,
    )

    empty_searches, filled_searches, \
    not_found_searches, skipped_searches = filter_searches(model_file, request.session['search_set_id'])

    context['progress_summary'] = {
        'Completed': '{0}/{1}'.format(filled_searches.count(),
                                      num_searches.count()),
        'Missing': '{0}/{1}'.format(not_found_searches.count(),
                                    num_searches.count()),
        'Skipped': '{0}/{1}'.format(skipped_searches.count(),
                                    num_searches.count()),
        'Remaining': '{0}/{1}'.format(empty_searches.count(),
                                      num_searches.count()),
    }

    # passes all the results from this file to the webpage
    file_results = md.Result.objects.filter(file=model_file,
                                            result__isnull=False)
    if file_results:
        context['results'] = file_results
        context['types'] = {}
        for result in file_results:
            # search_type = result.search.search_type
            # sub_type = result.search.sub_type
            # ----------- change --------------- #
            sts_model = md.StoredSearch.objects.get(id=result.storedsearch_id)
            result.search = sts_model
            # ----------- change end--------------- #
            search_type = result.search.search_type
            sub_type = result.search.sub_type

            if search_type in context['types'] and sub_type not in \
                    context['types'][search_type]:
                context['types'][search_type].append(sub_type)
            elif search_type not in context['types']:
                context['types'][search_type] = [sub_type, ]

    context['page'] = "review"
    return render(request, template, context)


@login_required()
def check_file_selected(request):
    """
    This function check for selected pdf file already present in the database or not.
    :return: True/False
    """
    file_path = request.GET.get('filename', None)
    filename_data = file_path.split("\\")
    file_name = filename_data[-1]
    is_selected = False
    obj = md.Result.objects.filter(file_id=file_name).order_by('-id')[0]
    searchset_id = obj.searchset_id
    file_obj = md.SearchSet.objects.filter(id=searchset_id)[0]
    if file_obj:
        file_path = str(file_obj.file_of_origin).split("\\")
        file_name = file_path[-1]
        is_selected = True
    data = {
        'is_selected': is_selected,
        'file_name': file_name
    }
    return JsonResponse(data)

@login_required()
def edit_cmp_description(request):
    """
    This function check for selected pdf file already present in the database or not.
    :return: True/False
    """
    cmp_description = request.GET.get('cmp_description')
    file = request.session['file']
    is_edited = True
    try:
        file_obj = md.File.objects.get(name=file)
        file_obj.company_description = cmp_description
        file_obj.save()
    except:
        is_edited = False
    data = {
        'is_edited': is_edited,
        'cmp_description': file_obj.company_description
    }
    return JsonResponse(data)

@login_required()
def change_country(request):
    """
    This function to select  pdf file on the basis of selected country.
    :return:
    """
    country_name = request.GET.get('countryName')
    # print("PATH_TO_PDF_FILES: ", PATH_TO_PDF_FILES)
    # print("country_name: ", country_name)
    path = ""
    if country_name == 'All':
        path = PATH_TO_PDF_FILES
    else:
        path = PATH_TO_PDF_FILES + '\\' + country_name

    file_form = FileForm(path, "pdf")
    file_form = str(file_form).replace("<tr><th></th><td>", "")\
        .replace('<select name="file" id="id_file">', '').replace("</select></td></tr>", "")
    if "option" not in file_form:
        file_form = "<option value='No results found....' disabled>No results found....</option>"
    option_html = file_form
    is_edited = True
    data = {
        'is_edited': is_edited,
        'country_name': country_name,
        'file_form':option_html
    }
    return JsonResponse(data)


@login_required()
def edit_member_firm_country(request):
    """
    This function to edit the source member firm/country.
    :return:
    """
    member_firm_country = request.GET.get('member_firm_country')
    member_firm_country_text = request.GET.get('member_firm_country_text')

    file = request.session['file']
    is_edited = True
    try:
        file_obj = md.File.objects.get(name=file)
        file_obj.source_country = member_firm_country
        file_obj.save()
    except Exception as e:
        is_edited = False
    data = {
        'is_edited': is_edited,
        'member_firm_country': member_firm_country_text  # file_obj.source_country
    }
    return JsonResponse(data)
