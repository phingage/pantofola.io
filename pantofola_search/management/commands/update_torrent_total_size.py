from pantofola_search.tools.torrent_fetcher import get_torrent_size_from_url
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pantofola_search.models import *
from datetime import datetime, timedelta


class Command(BaseCommand):
    args = 'limit'
    help = 'Update seed leech info'

    def handle(self, *args, **options):
        tor_cach_url = "http://torcache.kickass.safeproxy.me/torrent/%s.torrent"
        if len(args) > 1:
            max_torrents = args[0]
            filename = args[1]
        else:
            max_torrents = 1000
            filename = "/tmp/dailydump.txt"
        torrent_list = Torrent.objects.filter(total_size__exact=0)[:max_torrents]
        print len(torrent_list)
        if len(torrent_list)>0:
            with open(filename, 'r') as data_file:
                for line in data_file:
                    data_line = line.split("|")
                    try:
                        if data_line[2] == u"Movies":
                            magnet_link = data_line[0]
                            new_list = [x for x in torrent_list if x.pk == magnet_link]
                            if new_list:
                                print "Update ", magnet_link, " size:", data_line[5]
                                el = new_list[0]
                                el.total_size = data_line[5]
                                el.save()
                    except:
                        print "Wrong Data: ", data_line
        else:
            print "No 0 size torrents"
        print "Done"
                    # for t in torrent_list:
                    #     t_url = tor_cach_url % t.pk
                    #     print t_url
                    #     t.total_size = get_torrent_size_from_url(t_url)
                    #     t.save()
