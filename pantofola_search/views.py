# Create your views here.
from haystack.views import SearchView
from haystack.query import SearchQuerySet
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.core.cache import cache
from django.utils.encoding import uri_to_iri
from pantofola_search.models import Movie, Torrent
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.utils.translation import check_for_language, to_locale, get_language
from django.conf import settings
from django.utils.http import urlencode, urlquote_plus
import json

ht = {'it': 'ITA', 'de': 'GER', 'es': 'SPA', 'fr': 'FRA'}
reverse_ht = {'ITA': 'it', 'GER': 'de', 'SPA': 'es', 'FRA': 'fr', "FRE": 'fr', "SPE": 'es'}


def get_t_count():
    count_m = cache.get('count_m', 'no_m')
    if count_m == "no_m":
        count_m = Movie.objects.count()
        cache.set('count_m', count_m, 60 * 60)
    count_t = cache.get('count_t', 'no_t')
    if count_t == "no_t":
        count_t = Torrent.objects.count()
        cache.set('count_t', count_t, 60 * 60)
    return count_m, count_t


def set_lang(request, lang_code):
    response = HttpResponseRedirect("/")
    if lang_code and check_for_language(lang_code):
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
    return response


def show_all_movies(request):
    movies_all = Movie.objects.all()
    movies_count = len(movies_all)
    paginator = Paginator(movies_all, 25)
    page = request.GET.get('page')
    try:
        movies = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        movies = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        movies = paginator.page(paginator.num_pages)

    count_m, count_t = get_t_count()

    context = {'movies': movies,
               'movies_count': movies_count,
               'request': request,
               'n_movie': count_m,
               'n_torrent': count_t, }
    return render_to_response("pantofola_search/movies.html", context)


def show_movie(request, imdb_id):
    movie = get_object_or_404(Movie, pk=imdb_id)
    count_m, count_t = get_t_count()
    context = {'movie': movie,
               'request': request,
               'n_movie': count_m,
               'n_torrent': count_t, }
    return render_to_response("pantofola_search/single_movie.html", context)


def show_cp_api(request):
    response = {'results': [], 'total_results': 0}
    if request.method == 'POST':
        return HttpResponseBadRequest("POST not allowed")
    request_data = request.GET
    imdb_id = ""
    search = ""
    pulsar = "0"
    try:
        user = request_data['user']
        passkey = request_data['passkey']
        if 'imdbid' in request_data:
            imdb_id = request_data['imdbid']
        if 'search' in request_data:
            search = uri_to_iri(request_data['search'])
        if 'pulsar' in request_data:
            pulsar = request_data['pulsar']
    except KeyError:
        return HttpResponseBadRequest("Missing parameters")

    torrent_data = []
    site_name = request.META['HTTP_HOST']
    current_lang = get_language()
    if len(imdb_id) > 8:
        try:
            movie = Movie.objects.get(pk=imdb_id)
        except Movie.DoesNotExist:
            return HttpResponse(json.dumps(response), content_type="application/json")

        if current_lang in ht:
            mf = movie.torrent_set.filter(broken=False, seed__gt=0, language__exact=ht[current_lang])
        else:
            mf = movie.torrent_set.filter(broken=False, seed__gt=0)

        for t in mf:
            movie_title = movie.original_title
            movie_year = movie.year
            release_name = ".".join(
                [movie_title, str(movie_year), t.video_format, t.audio_source, t.video_source, t.video_codec])
            release_name.strip()
            release_name.replace(" ", ".")
            release_name += "-pantofola.io"
            magnet_link = "magnet:?xt=urn:btih:" + urlquote_plus(t.pk.upper())
            magnet_link += uri_to_iri(
                "&tr=udp://open.demonii.com:1337/announce&tr=udp://tracker.openbittorrent.com:80/announce&tr=udp://tracker.publicbt.com:80/announce&tr=udp://tracker.istole.it:80/announce")
            magnet_link += "&dn=" + urlquote_plus("[Pantofola.io] - ")
            if t.video_format:
                magnet_link += "[" + urlquote_plus(t.video_format) + "]"
            if len(t.audio_source):
                magnet_link += "[" + urlquote_plus(t.audio_source) + "]"
            if t.video_source:
                magnet_link += "[" + urlquote_plus(t.video_source) + "]"
            if t.video_codec:
                magnet_link += "[" + urlquote_plus(t.video_codec) + "]"
            magnet_link += "[" + urlquote_plus(movie_title) + "]"
            magnet_link += "[" + urlquote_plus(t.language) + "]"

            if pulsar == "0":
                torrent = {"release_name": release_name,
                           "torrent_id": t.pk,
                           "details_url": "http://" + site_name + "/title/" + imdb_id,
                           # "download_url": "http://torcache.net/torrent/" + t.pk.upper() + ".torrent",
                           "download_url": magnet_link,
                           "imdb_id": imdb_id,
                           "freeleech": True,
                           "type": "movie",
                           "size": int(t.total_size / 1048576.0),
                           "leechers": t.leech,
                           "seeders": t.seed
                           }
            else:
                # PULSAR OPTION
                torrent = {"name": release_name,
                           "info_hash": t.pk,
                           "uri": magnet_link,
                           "size": int(t.total_size / 1048576.0),
                           "seeds": int(t.seed),
                           "peers": int(t.leech),
                           "language": reverse_ht[t.language]
                           }
            torrent_data.append(torrent)
        response['results'] = torrent_data
        response['total_results'] = len(torrent_data)

    elif len(search) > 3:
        # Haystack query
        if current_lang in ht:
            query_result = SearchQuerySet().filter(content=search).filter(language=ht[current_lang]).filter(seed__gt=0)
        else:
            query_result = SearchQuerySet().filter(content=search).filter(seed__gt=0)

        for q in query_result:
            t = q.object
            imdb_id = q.imdb_id

            if pulsar== "0":

                torrent = {"release_name": t.original_name,
                           "torrent_id": t.pk,
                           "details_url": "http://" + site_name + "/title/" + imdb_id,
                           "download_url": "http://torcache.net/torrent/" + t.pk.upper() + ".torrent",
                           "imdb_id": imdb_id,
                           "freeleech": True,
                           "type": "movie",
                           "size": int(t.total_size / 1048576.0),
                           "leechers": t.leech,
                           "seeders": t.seed
                           }
            else:
                # PULSAR OPTION
                torrent = {"name": t.original_name,
                           "info_hash": t.pk,
                           "uri": "http://torcache.net/torrent/" + t.pk.upper() + ".torrent",
                           "size": int(t.total_size / 1048576.0),
                           "seeds": int(t.seed),
                           "peers": int(t.leech),
                           "language": reverse_ht[t.language]
                           }
            torrent_data.append(torrent)

        response['results'] = torrent_data
        response['total_results'] = len(torrent_data)

    return HttpResponse(json.dumps(response), content_type="application/json")




def show_movie_api(request, imdb_id):
    response_data = {'result': '200'}
    try:
        movie = Movie.objects.get(pk=imdb_id)
    except Movie.DoesNotExist:
        response_data['result'] = '404'
        response_data['data'] = []
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    movie_data = {"imdb_id": movie.pk, "original_title": movie.original_title}

    torrent_data = []

    current_lang = get_language()

    if current_lang in ht:
        mf = movie.torrent_set.filter(broken=False, seed__gt=0, language__exact=ht[current_lang])
    else:
        mf = movie.torrent_set.filter(broken=False, seed__gt=0)

    for t in mf:
        torrent = {"hash": t.pk, "size": t.total_size, "lang": t.language, "seed": t.seed,
                   "video_format": t.video_format, "video_codec": t.video_codec, "video_source": t.video_source,
                   "audio_source": t.audio_source}
        torrent_data.append(torrent)

    movie_data['torrents'] = torrent_data

    response_data['data'] = movie_data

    return HttpResponse(json.dumps(response_data), content_type="application/json")


class AggregateMoviesSearchView(SearchView):
    def build_page(self):
        return "", ""

    def extra_context(self):
        extra = super(AggregateMoviesSearchView, self).extra_context()

        sel_lang = ""
        if self.form.is_valid():
            extra['lang'] = self.form.cleaned_data['lang']
            if extra['lang'] is not None:
                sel_lang = extra['lang'].upper()
            extra['video_format'] = self.form.cleaned_data['video_format']
            extra['video_source'] = self.form.cleaned_data['video_source']
            extra['video_codec'] = self.form.cleaned_data['video_codec']
            extra['audio_source'] = self.form.cleaned_data['audio_source']
        # if self.results:
        # t_r = self.results
        #
        aggregate_result = {}
        first = True
        for single_query in self.results:
            # print len(aggregate_result)
            if len(aggregate_result) > 4:
                break

            fields = single_query.get_additional_fields()
            ftitle = False
            if sel_lang in fields:
                ftitle = fields[sel_lang]
            if single_query.imdb_id in aggregate_result:
                if single_query.seed > 0:
                    aggregate_result[single_query.imdb_id][0].append(single_query)
                else:
                    aggregate_result[single_query.imdb_id][1].append(single_query)

            else:
                if single_query.seed > 0:
                    aggregate_result[single_query.imdb_id] = [[single_query], [], ""]
                else:
                    aggregate_result[single_query.imdb_id] = [[], [single_query], ""]

            if ftitle:
                aggregate_result[single_query.imdb_id][2] = ftitle

        if aggregate_result:
            extra['aggregated_by_movie'] = aggregate_result
        else:
            try:
                extra['suggestion'] = self.results.query.spelling_suggestion
            except:
                extra['suggestion'] = ""

        return extra


    def create_response(self):
        """
        Generates the actual HttpResponse to send back to the user.
        """

        count_m, count_t = get_t_count()

        context = {
            'query': self.query,
            'n_movie': count_m,
            'n_torrent': count_t,
        }
        context.update(self.extra_context())
        # context['suggestion'] = self.results.query._spelling_suggestion
        response = render_to_response(self.template, context, context_instance=self.context_class(self.request))
        return response