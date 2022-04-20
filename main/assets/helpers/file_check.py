def check_for_file(request):
    """
    Checks if there is a file that is currently being used

    Args:
        request: the HTTP request

    Returns:The file if the file exists, else it returns false

    """

    if 'file' not in request.GET and 'file' not in request.session:
        return None
    elif 'file' in request.GET:
        file = request.GET['file']
    else:
        file = request.session['file']
    return file
