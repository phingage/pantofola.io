from django.core.management.base import BaseCommand, CommandError
from pantofola_search.models import *
from pantofola_search.tools.pantofola_fetcher import TorrentFetcher
from pantofola_search.tools.imdb_fetcher import ImdbFetcher
from _private import update_new_movie_info, check_for_title_in_db
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class Command(BaseCommand):
    args = '<kat_data_file> only_title(bool) limit default=False'
    help = 'Fetch a Kat data file'

    def handle(self, *args, **options):
        filename = args[0]
        o_title = False
        limit = False
        if len(args) > 1:
            limit = int(args[1])
        if len(args) > 2:
            o_title = True
        #data_file = open(filename, 'r')
        my_imdb = ImdbFetcher()
        myTorrent = TorrentFetcher()
        tot = 0
        with open(filename, 'r') as data_file:
            for line in data_file:
                data_line = line.split("|")
                try:
                    if data_line[2] == u"Movies":
                        movie_title = unicode(data_line[1], errors='ignore')
                        # movie_title = data_line[1]
                        # print movie_title
                        magnet_link = data_line[0]
                        # check if magnet already exist
                        if not Torrent.objects.filter(pk=magnet_link).exists() and not DeletedTorrent.objects.filter(
                                pk=magnet_link).exists():
                            kick_ass_link = data_line[3]
                            tor_cache_link = data_line[4]
                            file_size = data_line[5]
                            title_sanitized = myTorrent.sanitize_title(movie_title)
                            result = myTorrent.check_good_lenguage(title_sanitized)
                            if result:
                                self.stdout.write("Serving: %s" % data_line[1])
                                lang_tag = result
                                tags = myTorrent.extract_tag(title_sanitized)
                                clean_title = myTorrent.clean_title(movie_title)
                                self.stdout.write(clean_title)
                                broken = True
                                imdb_id = False
                                if not o_title:
                                    if len(clean_title) > 3:
                                        try:
                                            g_imdb_id = check_for_title_in_db(clean_title)
                                            if g_imdb_id:
                                                broken = False
                                                recheck = True
                                                clean_title = g_imdb_id
                                            else:
                                                imdb_id = my_imdb.query_a_title(clean_title)
                                                recheck = False
                                        except:
                                            recheck = True
                                    else:
                                        recheck = True
                                else:
                                    recheck = False

                                movie_title = movie_title if len(movie_title) < 188 else movie_title[:188]
                                clean_title = clean_title if len(clean_title) < 188 else clean_title[:188]



                                torrent = Torrent(torrent_id=magnet_link,
                                                  language=lang_tag,
                                                  movie=None,
                                                  score=0,
                                                  original_name=movie_title,
                                                  sanitized_name=clean_title,
                                                  video_source=tags[0],
                                                  video_format=tags[1],
                                                  video_codec=tags[2],
                                                  audio_source=tags[3],
                                                  total_size=file_size,
                                                  broken=broken,
                                                  ready_to_recheck=recheck)

                                torrent.save()
                                torrent.torrenturl_set.create(url=kick_ass_link, site="KAT")
                                torrent.torrenturl_set.create(url=tor_cache_link, site="TOR_CACHE")
                                torrent.save()
                                if imdb_id and not g_imdb_id:
                                    self.stdout.write(imdb_id)
                                    update_new_movie_info(clean_title, imdb_id, torrent)
                                imdb_id = False
                                tot += 1
                                if limit:
                                    if tot > limit:
                                        break
                except:
                    print "Wrong Data: ", data_line

