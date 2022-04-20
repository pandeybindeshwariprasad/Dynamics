"""
Assets represents the base Python processing section of the project. The code in here should be mostly
raw python and contains only the use of django functions or models. In this case assets refers to the
document processing backend and managers for handling the scanning process:

helpers: A group of functions are used one or more times in the project but do not fit inside a service
grouping.

loggers: This contains all the classes used to log processes and to track the success of file processing

services: This contains two sub-sections; processors and managers:

    managers: this is a group of classes that handle the managing of specific aspects of the
    user process, specifically Files, Elasticsearch, Sections and Stored Searches. Each of these has a
    respective manager class and there are some static methods that support these classes.

    processors: this is specifically the pdf processing backend. It handles the conversion of a PDF to a
    series of python objects that are indexed and tracked. It contains three processors; a processor to
    handle the whole PDF, a processor to handle each paragraph within the PDF and a processor to handle
    the construction of the index from the contents page.

"""