__author__ = 'armanini'

from django.core.management.base import BaseCommand, CommandError
from _private import check_for_title_in_db
from pantofola_search.models import *
from bingy import Search
from pantofola_search.tools.kickass_fetcher import KickAssFetcher
import sys
import re

reload(sys)
sys.setdefaultencoding('utf-8')


class Command(BaseCommand):
    help = 'Check broken torrent via bing'
    args = 'limit no_api'

    def handle(self, *args, **options):
        kFetcher = KickAssFetcher()
        limit = False
        stop_search = False
        if len(args) > 0:
            limit = int(args[0])
            print "Max entry: " + str(limit)
        if len(args) > 1:
            stop_search = False if (int(args[1])) < 1 else True
            print "Stop Search: " + str(stop_search)
        ready_to_bing = Torrent.objects.filter(ready_to_recheck__exact=False, broken=True, is_searched=False)
        now = 0
        for torrent in ready_to_bing:
            torrent_id = torrent.pk
            imdb_id = kFetcher.search(torrent_id)
            self.stdout.write("Serving: %s" % torrent.sanitized_name)

            if imdb_id:
                print "Founded: ", imdb_id
                self.stdout.write("Imdb: %s" % imdb_id)
                torrent.search_result = ""
                torrent.recheck_info = imdb_id
                torrent.is_search_result = False
                torrent.ready_to_recheck = True
                torrent.search_not_found = False
                torrent.is_searched = False
                torrent.save()
            else:
                print "Not Found"
                if stop_search:
                    torrent.search_not_found = True
                    torrent.is_searched = True
                    torrent.save()

            now += 1
            if limit:
                if limit < now:
                    break