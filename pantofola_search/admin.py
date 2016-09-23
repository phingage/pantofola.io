from django.contrib import admin
from pantofola_search.models import *
from django.utils.translation import ugettext_lazy as _
from pantofola_search.tools.pantofola_fetcher import TorrentFetcher


def remove_broken_status(modeladmin, request, queryset):
    queryset.update(broken=False, score=0.9)


remove_broken_status.short_description = "Unbroken Torrents"


def add_broken_status(modeladmin, request, queryset):
    queryset.update(broken=True)


add_broken_status.short_description = "Broken Torrents"


def ready_to_reprocessing(modeladmin, request, queryset):
    queryset.update(ready_to_recheck=True, is_searched=False, is_search_result=False, search_result='',
                    search_not_found=False)


ready_to_reprocessing.short_description = "Recheck Torrents"


def ready_to_rebing(modeladmin, request, queryset):
    queryset.update(ready_to_recheck=False, broken=True, is_searched=False,
                    is_search_result=False, search_result='', search_not_found=False)


ready_to_rebing.short_description = "ReSearch Torrents"


def void_reprocessing(modeladmin, request, queryset):
    queryset.update(ready_to_recheck=False)


void_reprocessing.short_description = "Un-Recheck Torrents"


def unlink_movie(modeladmin, request, queryset):
    queryset.update(movie=None)


unlink_movie.short_description = "Unlink Movie"


def unlink_unbroken_torrent(modeladmin, request, queryset):
    for obj in queryset:
        d_t = DeletedTorrent(torrent_id=obj.torrent_id, original_name=obj.original_name)
        d_t.save()
    queryset.delete()


unlink_unbroken_torrent.short_description = "Forgot them!"


def sanitized_torrent(modeladmin, request, queryset):
    myTorrent = TorrentFetcher()
    for obj in queryset:
        obj.sanitized_name= myTorrent.clean_title(obj.sanitized_name)
        obj.save()

sanitized_torrent.short_description = "Sanitize title"


def square_brackets(modeladmin, request, queryset):
    queryset.update(sanitized_name='[', ready_to_recheck=True)


square_brackets.short_description = "Square Brackets"


class BrokenAndNoSeed(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Only Broken 0 Seed')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'yes_no'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('yes', _('Yes')),
            ('no', _('No')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'yes':
            return queryset.filter(broken=True, seed__exact=-1)
        if self.value() == 'no':
            return queryset.filter(broken=False, seed__gte=0)  # birthday__lte=date(1999, 12, 31))


class ForeignTitleInLine(admin.TabularInline):
    model = ForeignTitle
    extra = 1


class TitleInLine(admin.TabularInline):
    model = Title
    extra = 1


class TorrentInLine(admin.TabularInline):
    model = Torrent
    extra = 1


class TorrentUrlInLine(admin.TabularInline):
    model = TorrentUrl
    extra = 1


class TorrentAdmin(admin.ModelAdmin):
    list_display = (
        'original_name', 'date_added', 'score', 'sanitized_name', 'recheck_info', 'movie', 'language', 'has_good_score')
    list_filter = ('broken', 'ready_to_recheck', 'language', 'is_search_result', 'search_not_found', BrokenAndNoSeed)
    search_fields = ['original_name', 'sanitized_name', 'movie__original_title']
    list_editable = ['sanitized_name', 'recheck_info']
    inlines = [TorrentUrlInLine]
    actions = [add_broken_status, remove_broken_status, ready_to_reprocessing, ready_to_rebing, void_reprocessing,
               unlink_movie, unlink_unbroken_torrent,sanitized_torrent]


class MovieAdmin(admin.ModelAdmin):
    list_display = ('original_title', 'imdb_id', 'year', 'torrents_count')
    search_fields = ['original_title', 'imdb_id']
    inlines = [ForeignTitleInLine, TitleInLine, TorrentInLine]


admin.site.register(Movie, MovieAdmin)
admin.site.register(Torrent, TorrentAdmin)
admin.site.register(DeletedTorrent)