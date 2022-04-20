import pandas as pd
import logging
from main.models import SapData

logger = logging.getLogger(__name__)

# TODO: MAKE THIS WORK PROPERLY

def sap_excel_import(excel_doc_path):
    """
    Import sap from an uploaded excel file.
    Args:
        excel_doc_path: the path to the excel file

    Returns:

    """

    logger.info("Importing the SAP extract {0}".format(excel_doc_path))
    df = pd.read_excel(excel_doc_path)
    df.columns = ['year', 'billing_partner', 'master_profit_centre', 'project', 'project_name', 'project_customer_no',
                  'project_customer', 'g_m_uhc', 'cust_industry', 'g_m_pe', 'g_m_uhc_industry', 'g_m_uhc_subindustry',
                  'sector', 'industry', 'customer_type', 'slc_code', 'g_m_uhc_segmt', 'uhc', 'uhc_number',
                  'gross_revenue', 'provisions', 'net_services', 'product_sales', 'other_revenue', 'net_revenue', 'rrr']

    file_name_list = str(excel_doc_path).rsplit('\\', 1)
    df['file_name'] = file_name_list[1]

    # create dict to upload to model
    df_final = df.to_dict('records')

    # create dict from existing records db
    existing_db = SapData.objects.values('year', 'billing_partner', 'master_profit_centre', 'project',
                                              'project_name','project_customer_no', 'project_customer', 'g_m_uhc',
                                              'cust_industry', 'g_m_pe', 'g_m_uhc_industry', 'g_m_uhc_subindustry',
                                              'sector', 'industry', 'customer_type', 'slc_code', 'g_m_uhc_segmt', 'uhc',
                                              'uhc_number', 'gross_revenue', 'provisions', 'net_services',
                                              'product_sales', 'other_revenue', 'net_revenue', 'rrr', 'file_name')

    # create dict for records not existing in db
    # df_upload = [x for x in df_final if x not in list(existing_db)]


    return df_final
