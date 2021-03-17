from django import template
from django.utils.html import mark_safe

import markdown

register = template.Library()

@register.filter(name='markdown')
def filter_markdown(value):
    return mark_safe(markdown.markdown(value))

@register.filter
def nopar(value):
    return mark_safe(value.replace('<p>', '').replace('</p>', ''))
