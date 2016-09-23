from haystack import indexes
from pantofola_search.models import Movie, Title, Torrent
from celery_haystack.indexes import CelerySearchIndex


class TorrentIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    language = indexes.CharField(model_attr='language', indexed=False)
    video_format = indexes.CharField(model_attr='video_format')
    video_codec = indexes.CharField(model_attr='video_codec')
    video_source = indexes.CharField(model_attr='video_source')
    audio_source = indexes.CharField(model_attr='audio_source')
    seed = indexes.IntegerField(model_attr='seed', indexed=False)
    leech = indexes.IntegerField(model_attr='leech', indexed=False)
    total_size = indexes.IntegerField(model_attr='total_size', indexed=False)
    is_broken = indexes.BooleanField(model_attr="broken", indexed=False)

    def get_model(self):
        return Torrent

    def get_updated_field(self):
        return "date_modified"

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(broken__exact=False)

    def prepare(self, obj):
        self.prepared_data = super(TorrentIndex, self).prepare(obj)
        related_movie = obj.movie
        if related_movie:
            self.prepared_data['year'] = related_movie.year
            self.prepared_data['imdb_id'] = related_movie.pk
            self.prepared_data['original_title'] = related_movie.original_title
            self.prepared_data['aka'] = [t.title for t in related_movie.title_set.all()]
            for lang in related_movie.foreigntitle_set.all():
                self.prepared_data[lang.language] = lang.title
        else:
            self.prepared_data = {}
        return self.prepared_data
