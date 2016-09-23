__author__ = 'armanini'

from django.core.management.base import BaseCommand, CommandError
from _private import check_for_title_in_db
from pantofola_search.models import *
from bingy import Search
from pantofola_search.tools.pantofola_fetcher import TorrentFetcher
import sys
import re

reload(sys)
sys.setdefaultencoding('utf-8')


class Command(BaseCommand):
    help = 'Check broken torrent via bing'
    args = 'limit no_api'

    def handle(self, *args, **options):
        myTorrent = TorrentFetcher()
        limit = False
        re_clean = False
        api = True
        if len(args) > 0:
            limit = int(args[0])
            print "Max entry: " + str(limit)
        if len(args) > 1:
            api = False if (int(args[1])) < 1 else True
            print "Use api: " + str(api)
        if len(args) > 2:
            re_clean = False if int(args[2]) < 1 else True
            print "Recheck Clean Name: " + str(re_clean)

        ready_to_bing = Torrent.objects.filter(ready_to_recheck__exact=False, broken=True, is_searched=False)
        bs = Search()
        imdb_re = re.compile(r'(?P<imdb_id>tt\d{7})', flags=re.IGNORECASE + re.MULTILINE)
        now = 0
        for torrent in ready_to_bing:
            if re_clean:
                clean_title = myTorrent.clean_title(torrent.original_name)
            else:
                clean_title = myTorrent.clean_title(torrent.sanitized_name)
            torrent.sanitized_name = clean_title
            self.stdout.write("Serving: %s" % clean_title)

            g_imdb_id = check_for_title_in_db(clean_title)
            b_r = False
            if not g_imdb_id:
                search_q = clean_title + " site:imdb.com"
                b_r = bs.query(search_q, api, False)
            if b_r or g_imdb_id:
                url = ''
                if b_r:
                    for u in b_r:
                        res = imdb_re.search(u[0])
                        if res:
                            url = u[0]
                            break
                if g_imdb_id:
                    url = g_imdb_id
                if url:
                    self.stdout.write("Imdb: %s" % url)
                    torrent.search_result = url
                    torrent.is_search_result = True
                    torrent.ready_to_recheck = True
                    torrent.search_not_found = False
                    torrent.is_searched = True
                    torrent.save()
                else:
                    torrent.search_not_found = True
                    torrent.is_searched = True
                    torrent.save()
            else:
                torrent.search_not_found = True
                torrent.is_searched = True
                torrent.save()

            now += 1
            if limit:
                if limit < now:
                    break