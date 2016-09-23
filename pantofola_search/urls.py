from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from haystack.views import SearchView
from pantofola_search.views import AggregateMoviesSearchView
from pantofola_search.forms import MovieSearchByLanguageForm
from pantofola_search.views import show_all_movies, show_movie, show_movie_api, set_lang, show_cp_api
from django.views.decorators.cache import cache_page


admin.autodiscover()

urlpatterns = patterns('',
       # Examples:

       url(r'^search/$', AggregateMoviesSearchView(form_class=MovieSearchByLanguageForm,
                                                   template="pantofola_search/list_view.html",
                                                   load_all=False), name='pantofola_search_result'),
       url(r'^$', AggregateMoviesSearchView(form_class=MovieSearchByLanguageForm,
                                            template="pantofola_search/index.html", load_all=False),
           name='pantofola_search_home'),
       # url(r'^pantofola/', include('pantofola.pantofola.urls')),

       url(r'^set/(?P<lang_code>[a-z]{2})/$', set_lang, name="set_lang"),
       url(r'^title/$', cache_page(60 * 60 * 24)(show_all_movies), name="all_movies"),
       url(r'^title/(?P<imdb_id>tt\d{7})/$', cache_page(60 * 60 * 24)(show_movie), name='single_movie'),

       url(r'^api/title/(?P<imdb_id>tt\d{7})/$', cache_page(60 * 15)(show_movie_api), name='single_movie_api'),
       url(r'^cp/$', cache_page(60 * 15)(show_cp_api), name='single_cp_api')

)
