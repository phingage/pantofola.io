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

    def handle(self, *args, **options):
        f = open('broken.csv', 'w')
        t_fetch = TorrentFetcher()
        broken_torrents = Torrent.objects.filter(broken=True)
        for torrent in broken_torrents:
            print torrent.sanitized_name, t_fetch.clean_title(torrent.sanitized_name)
            f.write(torrent.pk+"::"+torrent.original_name+"::"+torrent.sanitized_name+"::\n")
        f.close()
