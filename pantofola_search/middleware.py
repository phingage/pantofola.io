__author__ = 'armanini'
from django.conf import settings
from django.utils import translation
from collections import OrderedDict as SortedDict
try:
    from django.utils.translation import LANGUAGE_SESSION_KEY
    over_one_seven = True
except ImportError:
    over_one_seven = False


class LangInDomainMiddleware(object):
    """
    Middleware for determining site's language via the domain name used in
    the request.
    This needs to be installed after the LocaleMiddleware so it can override
    that middleware's decisions.
    """

    def __init__(self):
        self._supported_languages = SortedDict(settings.LANGUAGES)
        self._language_domains = SortedDict(settings.MULTILANG_LANGUAGE_DOMAINS)

    def process_request(self, request):
        lang_code = translation.get_language_from_path(request.path_info)
        if lang_code is not None:
            return

        if over_one_seven:
            if hasattr(request, 'session'):
                if over_one_seven:
                    lang_code = request.session.get(LANGUAGE_SESSION_KEY, None)
                else:
                    lang_code = request.session.get('django_language', None)
                if lang_code is not None:
                    return

        lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if lang_code is not None:
            return

        try:
            lang = self._language_domains[request.META['HTTP_HOST']]
            translation.activate(lang)
            request.LANGUAGE_CODE = translation.get_language()
        except KeyError:
            pass