__author__ = 'armanini'

from django.core.management.base import BaseCommand, CommandError
from pantofola_search.models import *
from pantofola_search.tools.imdb_fetcher import ImdbFetcher
from pantofola_search.tools.pantofola_fetcher import TorrentFetcher
from _private import update_new_movie_info
import re

import sys
from _private import check_for_title_in_db

reload(sys)
sys.setdefaultencoding('utf-8')


class Command(BaseCommand):
    help = 'Generate File of broken torrent'

    def add_arguments(self, parser):
        parser.add_argument('file_name')

    def handle(self, *args, **options):
        t_fetch = TorrentFetcher()
        file_name = options['file_name']
        f = open(file_name, 'r')
        for line in f:
            info = line.split("::")
            torrent_id = info[0]
            clean_title = info[2]
            print clean_title
            imdb = info[3]
            print "IMDB: ", imdb
            try:
                torrent = Torrent.objects.get(pk=torrent_id)
                torrent.is_search_result = True
                torrent.ready_to_recheck = True
                torrent.recheck_info = imdb
                torrent.search_result = ''
                torrent.sanitized_name = clean_title
                torrent.is_searched = True
                torrent.save()
            except:
                print "Torrent Error"
