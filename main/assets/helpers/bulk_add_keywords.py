import pandas as pd
import logging
from main.models import Keyword

logger = logging.getLogger(__name__)

def excel_import(excel_doc_path):
    """
    Import keywords from an uploaded keyword file.
    Args:
        excel_doc_path: the path to the keyword file

    Returns:

    """
    logger.info("Importing the keyword file {0}".format(excel_doc_path))
    df = pd.read_excel(excel_doc_path,
                       encoding='utf-8',
                       error_bad_lines=False,)
    created_set = None
    for row in df.iterrows():
        alts = None
        row = row[1].dropna()
        if len(row) > 1:
            alts = list(row.values)
        if alts:
            created_set = Keyword.create_keyword_set(alts)
    return created_set


def list_upload(keyword_list):
    """
    Create a set of keywords from a list.
    Args:
        keyword_list: the list of keywords that are alternate

    Returns: the keyword list

    """
    created_set = Keyword.create_keyword_set(keyword_list)
    return created_set
