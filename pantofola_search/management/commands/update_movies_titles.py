from django.db.models import Count
from pantofola_search.tools.imdb_fetcher import ImdbFetcher
from pantofola_search.tools.tracker_scarper import get_leech_seed_data
from django.core.management.base import BaseCommand, CommandError
from pantofola_search.models import *
from datetime import timedelta
from django.utils.timezone import now

__author__ = 'armanini'


class Command(BaseCommand):
    help = 'Update seed leech info'

    def handle(self, *args, **options):
        movies = Movie.objects.annotate(num_titles=Count('foreigntitle')).filter(num_titles__lte=0)
        print "START CHECK FOR ", len(movies), " MOVIES"
        for movie in movies:
            print "Fetch ", movie
            my_imdb = ImdbFetcher()
            movie_info = my_imdb.query_movie_info(movie.imdb_id, movie.original_title)
            if len(movie_info[3][2]) > 0:
                print "Movie info: ", movie_info[3][2]
                for forg in movie_info[3][2]:
                    movie.foreigntitle_set.create(title=forg[0], language=forg[1])
            else:
                print "Not found"
                movie.foreigntitle_set.create(title=movie.original_title, language="UNK")
        print "done"