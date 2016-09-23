__author__ = 'armanini'
from django import template
from pantofola_search.models import Movie

register = template.Library()

ht = {'it': 'ITA', 'de': 'GER', 'es': 'SPA', 'fr': 'FRA'}


@register.filter
def get_title(movie, locale):
    """Removes all values of arg from the given string"""
    if isinstance(movie, Movie):
        if locale in ht:
            local_titles = movie.foreigntitle_set.filter(language__exact=ht[locale])
            if local_titles:
                return local_titles[0].title
            else:
                return movie.original_title
        else:
            return movie.original_title
    else:
        return ""