import re
from django import template


register = template.Library()


@register.filter(name='check_number')
def check_number(x):
    # write a function to check if a string is numeric
    if re.search(r'[0-9]+', x):
        return True
    else:
        return False


@register.filter(name='check_keyword')
def check_number(x):
    # write a function to check if a string is numeric
    if re.search(r'[*]', x):
        return True
    else:
        return False
