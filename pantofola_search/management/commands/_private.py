from pantofola_search.models import *
from pantofola_search.tools.imdb_fetcher import ImdbFetcher


def update_new_movie_info(clean_title, imdb_id, torrent, is_imdb=False):
    my_imdb = ImdbFetcher()
    if not Movie.objects.filter(pk=imdb_id).exists():
        # #[imdb_id,year,max_ratio,[titles[1]]]
        movie_info = my_imdb.query_movie_info(imdb_id, clean_title)
        movie = Movie(imdb_id=movie_info[0],
                      year=movie_info[1],
                      original_title=movie_info[3][0])
        movie.save()
        for aka in movie_info[3][1]:
            movie.title_set.create(title=aka)
        for forg in movie_info[3][2]:
            movie.foreigntitle_set.create(title=forg[0], language=forg[1])
        max_ratio = movie_info[2]
        # print movie_info, tags, lang_tag
    else:
        movie = Movie.objects.get(pk=imdb_id)
        score_title = [movie.original_title]
        for aka_q in movie.title_set.all():
            score_title.append(aka_q.title)
        max_ratio = my_imdb.compute_score(clean_title, score_title)
    alarm_ratio = False
    if float(max_ratio) < 0.5 and not is_imdb:
        alarm_ratio = True
    torrent.movie = movie
    torrent.score = max_ratio
    torrent.broken = alarm_ratio
    # torrent.ready_to_recheck = False
    if is_imdb:
        #torrent.sanitized_name = movie.original_title
        torrent.score = 1
        torrent.broken = False
    torrent.save()


def check_for_title_in_db(clean_title):
    t_e = Torrent.objects.filter(sanitized_name__exact=clean_title,
                                 broken=False, ready_to_recheck=False).first()
    if t_e:
        return t_e.movie.imdb_id
    else:
        return None