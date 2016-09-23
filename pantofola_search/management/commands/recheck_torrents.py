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
    help = 'Recheck Modified Torrents'

    def handle(self, *args, **options):
        ready_to_recheck = Torrent.objects.filter(ready_to_recheck__exact=True)
        imdb_re = re.compile(r'(?P<imdb_id>tt\d{7})', flags=re.IGNORECASE)
        my_imdb = ImdbFetcher()
        t_fetch = TorrentFetcher()
        for torrent in ready_to_recheck:
            clean_title = torrent.sanitized_name
            recheck_info = torrent.recheck_info
            self.stdout.write("Serving: %s" % clean_title)

            if recheck_info == '-':
                d_t = DeletedTorrent(torrent_id=torrent.torrent_id, original_name=torrent.original_name)
                d_t.save()
                torrent.delete()
                continue
            if recheck_info == '+':
                torrent.ready_to_recheck = False
                torrent.broken = False
                torrent.score = 0.9
                torrent.save()
                continue
            #
            # if clean_title == '[':
            # original_t = torrent.original_name
            #     new_title = re.sub(ur"^\[.*?\]|^\(.*?\)", ' ', original_t)
            #     clean_title = t_fetch.clean_title(t_fetch.sanitize_title(new_title))
            #     torrent.sanitized_name = clean_title
            #     torrent.save()

            if ((len(clean_title) < 3 or clean_title == ' ') and len(torrent.search_result) < 9) and not recheck_info:
                continue

            imdb_id = False
            is_search = False
            if torrent.is_search_result:
                imdb_res = imdb_re.search(torrent.search_result)
                is_search = True

            else:
                g_imdb_id = check_for_title_in_db(clean_title)
                if g_imdb_id:
                    recheck_info = g_imdb_id
                imdb_res = imdb_re.search(recheck_info)

            if imdb_res:
                imdb_id = imdb_res.group('imdb_id')
                if not is_search:
                    is_imdb = True
                else:
                    is_imdb = False
            else:
                #imdb_id = my_imdb.query_a_title(clean_title)
                is_imdb = False

            if imdb_id:
                self.stdout.write(imdb_id)
                torrent.ready_to_recheck = False
                torrent.date_added = datetime.now()
                torrent.save()
                update_new_movie_info(clean_title, imdb_id, torrent, is_imdb)
