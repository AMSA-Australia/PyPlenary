from django import template
from django.utils.html import escape, mark_safe

register = template.Library()

@register.filter
def timeline_time(value):
    return mark_safe(escape(value).replace('–', '<br>–'))
