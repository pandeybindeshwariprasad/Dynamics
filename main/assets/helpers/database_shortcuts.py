from django.db.models import Q
import main.models as md


def filter_searches(model_file, searchset_id=None):
    """
    Query the database to filter and arrange the searches for this doc
    based on the results that have been submitted
    Args:
        model_file: the file that is active
        searchset_id: Id of file type
    Returns: 4 QuerySets; one for each possible condition of a search

    """
    # The empty searches
    if searchset_id is not None:
        empty_results = md.Result.objects.filter(
            file=model_file,
            result__isnull=True, searchset_id=searchset_id
        ).distinct()
        empty_searches = md.StoredSearch.objects.filter(
            result__in=empty_results, searchset_id=searchset_id
        )

    else:
        empty_results = md.Result.objects.filter(
            file=model_file,
            result__isnull=True).distinct()
        # empty_searches = md.StoredSearch.objects.filter(
        #     result__in=empty_results)
        empty_searches = empty_results

    # The filled in results
    if searchset_id is not None:
        filled_results = md.Result.objects.filter(
            ~Q(result__exact=""),
            ~Q(result__exact="TBC"),
            file=model_file,
            result__isnull=False, searchset_id=searchset_id
        ).distinct()
        filled_searches = md.StoredSearch.objects.filter(
            result__in=filled_results, searchset_id=searchset_id
        )
    else:
        filled_results = md.Result.objects.filter(
            ~Q(result__exact=""),
            ~Q(result__exact="TBC"),
            file=model_file,
            result__isnull=False).distinct()
        # filled_searches = md.StoredSearch.objects.filter(
        #     result__in=filled_results)
        filled_searches = filled_results

    # The N/A'd results
    if searchset_id is not None:
        not_found_results = md.Result.objects.filter(
            file=model_file,
            result__isnull=False,
            result__exact="", searchset_id=searchset_id
        ).distinct()
        not_found_searches = md.StoredSearch.objects.filter(
            result__in=not_found_results, searchset_id=searchset_id
        )
    else:
        not_found_results = md.Result.objects.filter(
            file=model_file,
            result__isnull=False,
            result__exact="").distinct()
        # not_found_searches = md.StoredSearch.objects.filter(
        #     result__in=not_found_results)
        not_found_searches = not_found_results
    # The skipped results
    if searchset_id is not None:

        skipped_results = md.Result.objects.filter(
            file=model_file,
            result__isnull=False,
            result__exact="TBC", searchset_id=searchset_id
        ).distinct()
        skipped_searches = md.StoredSearch.objects.filter(
            result__in=skipped_results, searchset_id=searchset_id
        )
    else:
        skipped_results = md.Result.objects.filter(
            file=model_file,
            result__isnull=False,
            result__exact="TBC").distinct()
        # skipped_searches = md.StoredSearch.objects.filter(
        #     result__in=skipped_results)
        skipped_searches = skipped_results


    return empty_searches, filled_searches, \
        not_found_searches, skipped_searches
