from django.db import models
from datetime import datetime

annunce_site = ["udp://open.demonii.com:1337/announce",
                "udp://tracker.openbittorrent.com:80/announce",
                "udp://tracker.publicbt.com:80/announce",
                "udp://tracker.istole.it:80/announce"]

# Create your models here.
class Movie(models.Model):
    imdb_id = models.CharField(max_length=10, primary_key=True)
    original_title = models.CharField(max_length=255)
    year = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)

    def torrents_count(self):
        return len(self.torrent_set.all())

    def __unicode__(self):
        return self.imdb_id + " - " + self.original_title + " (" + str(self.year) + ")"


class Title(models.Model):
    movie = models.ForeignKey("Movie")
    title = models.CharField(max_length=255)

    def __unicode__(self):
        return self.title


class ForeignTitle(models.Model):
    movie = models.ForeignKey("Movie")
    title = models.CharField(max_length=255)
    language = models.CharField(max_length=255, default="ITA")

    def __unicode__(self):
        return self.title + " - " + self.language


class Torrent(models.Model):
    torrent_id = models.CharField(max_length=255, primary_key=True)
    movie = models.ForeignKey("Movie", blank=True, null=True)
    language = models.CharField(max_length=255, default="ITA")
    score = models.FloatField(blank=True)
    original_name = models.CharField(max_length=255)
    sanitized_name = models.CharField(max_length=255)
    recheck_info = models.CharField(max_length=255, default='', blank=True, null=True)
    video_format = models.CharField(max_length=255, blank=True)
    video_codec = models.CharField(max_length=255, blank=True)
    video_source = models.CharField(max_length=255, blank=True)
    audio_source = models.CharField(max_length=255, blank=True)
    broken = models.BooleanField(default=False)
    ready_to_recheck = models.BooleanField(default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    seed = models.IntegerField(default=0)
    leech = models.IntegerField(default=0)
    seed_last_update = models.DateTimeField(default=datetime.fromtimestamp(1))
    total_size = models.BigIntegerField(default=0)
    search_result = models.CharField(max_length=255, default='', blank=True, null=True)
    is_search_result = models.BooleanField(default=False)
    is_searched = models.BooleanField(default=False)
    search_not_found = models.BooleanField(default=False)

    class Meta:
        ordering = ["-seed", "-total_size"]


    def has_good_score(self):
        return self.score >= 0.5

    @property
    def get_trackers(selfs):
        return '&tr='.join(annunce_site)

    has_good_score.admin_order_field = 'score'
    has_good_score.boolean = True
    has_good_score.short_description = 'Has good score?'

    def __unicode__(self):
        return self.torrent_id + " - " + self.original_name


class DeletedTorrent(models.Model):
    torrent_id = models.CharField(max_length=255, primary_key=True)
    original_name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.torrent_id + " - " + self.original_name


class TorrentUrl(models.Model):
    url = models.URLField()
    site = models.CharField(max_length=255)
    torrent = models.ForeignKey("Torrent")

    def __unicode__(self):
        return self.url + " - " + self.site