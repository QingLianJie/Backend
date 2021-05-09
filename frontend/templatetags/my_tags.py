import markdown
from django import template

register = template.Library()


@register.filter
def format_term(value:str):
    return "term"+value.replace('-','_')


@register.filter
def to_markdown(text):
    return markdown.markdown(text, extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.toc',
    ])


@register.filter
def page_range(num):
    return [i-num//2 for i in range(num)]
