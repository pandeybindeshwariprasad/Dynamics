import os

from django import forms
from main import models
from Deloitte_Dynamics.settings import PATH_TO_PDF_FILES

# ----
# -----

class KeywordForm(forms.Form):
    """
    A form to search for keywords.

    Fields:
        keywords: a CharField that contains a list of keywords separated
        by a comma.
    """
    keywords = forms.CharField(label="", max_length=140)


class DescriptionSelectionForm(forms.Form):
    """
    This form is for selecting a search from the active search set, the
    searches are sorted into empty, filled, not found and skipped. On
    selection, this form submits.

    Fields:
        search: a ChoiceField displaying all the searches, sorted as
        above.
    """
    def __init__(self, empty, filled, initial, not_found, skipped):
        super(DescriptionSelectionForm, self).__init__(initial)
        self.empty = empty
        self.filled = filled
        self.not_found = not_found
        self.skipped = skipped
        sorted_search_lists = {
            'Incomplete': self.empty,
            'Skipped': self.skipped,
            'Not Found': self.not_found,
            'Complete': self.filled,
        }
        choices = []

        for key, search_list in sorted_search_lists.items():
            if sorted_search_lists[key]:
                sub_choices = [(search['description'],
                                search['description'])
                               for search in search_list]
                choices.append(
                    (key,
                     sub_choices)
                )

        search = forms.ChoiceField(choices=choices, )
        search.widget.attrs.update({'onchange': 'this.form.submit()'})
        search.widget.attrs.update({'style': "max-width:50%;"})
        self.fields['search'] = search


# This is the form for inputting the results that have been found
class ResultForm(forms.Form):
    """
    This form is for inputting results that have been found. It takes
    the result, unit and timestamp. The width of these inputs is hard
    coded to 70 pixels.

    Fields:
        result: a CharField for the value of the result
        unit: a CharField for the unit of the result
        result: a CharField for the timestamp of the result

    """
    input_widget = forms.TextInput(attrs={'style': 'width: 70px'})
    result = forms.CharField(max_length=140, label='Result',
                             widget=input_widget, required=False)
    unit = forms.CharField(max_length=140, label='Unit',
                            widget=input_widget, required=False)
    timestamp = forms.CharField(max_length=140, label='Timestamp',
                                widget=input_widget, required=False)
    notes = forms.CharField(max_length=140, label='Notes',
                            widget=input_widget, required=False)


# This is the form to add a new set of alternative keywords
class AlternativesForm(forms.Form):
    """
    This form is for inputting an alternative keyword.

    Fields:
        alternative_keyword: a CharField for the keyword being added
    """
    alternative_keyword = forms.CharField(label="",
                                          max_length=200)


class FileForm(forms.Form):
    def __init__(self, path, extension, prefix=None, check_box=False, country_form=False, **kwargs):
        """
        This form is for selecting files/folders. It has an optional
        checkbox and must be passed the desired file extension. It
        only displays paths with the given extension.

        Fields:
            file: a FilePathField for the file that is being selected
            check: a BooleanField for the (optional) check box.
            country:

        """
        super(FileForm, self).__init__(**kwargs)
        file = forms.FilePathField(label='',
                                   path=path,
                                   allow_files=True,
                                   recursive=True)

        # country_obj = [(cnt_mdl.country_name, cnt_mdl.country_name) for cnt_mdl in models.Country.objects.all()]
        # country_obj = [('All', 'All')] + country_obj
        # country = forms.ChoiceField(label='', choices=country_obj)
        choices = []
        # country_choices = ["UK", "Canada"]
        # country.widget.choices = country_choices
        sub_folders = {}
        for path, name in file.choices:
            if path.endswith(".{}".format(extension)):
                name = name.strip(r"\\")
                if "\\" in name:
                    stages = os.path.split(name)
                    folder = stages[0]
                    name = "\\".join(stages[1:])
                    if folder not in sub_folders:
                        sub_folders[folder] = []
                    sub_folders[folder].append((path, name))
                else:
                    choices.append((path, name))
        for i, folder in enumerate(sub_folders):
            choices.append((folder, sub_folders[folder]))
        file.widget.choices = choices

        # file.widget.attrs.update(
        #     {'data-live-search': 'true', 'class': "selectpicker"})
        # file.widget.attrs.update(
        #     {'class': 'selectpicker show-tick form-control', 'data-live-search': "true"})

        if prefix:
            self.fields['{}_file'.format(prefix)] = file
        elif country_form == False:
            self.fields['file'] = file
        if check_box:
            self.fields['check'] = forms.BooleanField(label=check_box,
                                                      required=False)
        if country_form == True:
            opration_country_object = models.Country.objects.all()
            # ------------------------------------------------- #
            country_obj = [('All', 'All')]
            for row in opration_country_object:
                country_obj.append((row.Alpha_3_code, str(row.Country + "-" + row.Alpha_3_code)))
            country = forms.ChoiceField(label='', choices=country_obj)

            self.fields['country'] = country
