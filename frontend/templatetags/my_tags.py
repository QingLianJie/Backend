from django import template

register = template.Library()

@register.filter
def format_term(value:str):
    return "term"+value.replace('-','_')