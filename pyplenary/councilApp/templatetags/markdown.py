from django import template
from django.utils.html import mark_safe

import markdown

register = template.Library()

@register.filter(name='markdown')
def filter_markdown(value):
    # FIXME: Make this not cursed
    return mark_safe(markdown.markdown(value).replace('<a ', '<a target="_blank" '))

@register.filter
def nopar(value):
    # FIXME: Make this not cursed
    return mark_safe(value.replace('<p>', '').replace('</p>', ''))
