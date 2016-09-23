from pantofola_search.tools.tracker_scarper import get_leech_seed_data
from django.core.management.base import BaseCommand, CommandError
from pantofola_search.models import *
from datetime import timedelta
from django.utils.timezone import now


class Command(BaseCommand):
    args = 'limit min_h'
    help = 'Update seed leech info'

    def process_block(self, t_cut_list):
        t_scarpe = ["udp://open.demonii.com:1337/announce",
                "udp://tracker.openbittorrent.com:80/announce",
                "udp://tracker.publicbt.com:80/announce",
                "udp://tracker.istole.it:80/announce",
                "udp://tracker.coppersurfer.tk:6969/announce",
                "udp://tracker.leechers-paradise.org:6969/announce"]
        torrent_list =[t.pk for t in t_cut_list]
        data = get_leech_seed_data(t_scarpe, torrent_list)
        for torrent in t_cut_list:
            torrent.seed = data[torrent.pk]['seed'] if data[torrent.pk]['seed'] > 0 else -1
            torrent.leech = data[torrent.pk]['peers'] if data[torrent.pk]['peers'] > 0 else -1
            torrent.seed_last_update=now()
            torrent.save()
        print data


    def handle(self, *args, **options):
        scarpe_all = False
        reuqest_per_query = 50
        if len(args) > 1:
            max_torrents = int(args[0])
            min_h = int(args[1])
        else:
            max_torrents = 50000
            min_h = 6
            scarpe_all = True
        min_date = now()-timedelta(hours=float(min_h))
        list_size = len(range(0, max_torrents, reuqest_per_query))

        for i in range(list_size):
            if scarpe_all:
                t_cut_list = Torrent.objects.filter(seed_last_update__lt=min_date)[:reuqest_per_query]
            else:
                t_cut_list = Torrent.objects.filter(seed_last_update__lt=min_date, seed__gt=-2)[:reuqest_per_query]
            if not t_cut_list:
                break
            self.process_block(t_cut_list)

        print "done"
