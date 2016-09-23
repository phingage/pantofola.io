# coding: utf-8

from pulsar import provider

# Set language: it, es, de, fr, en==any language
# Set passkey
# Set username

__LANGUAGE__ = "en"
__PASS_KEY__ = "dev"
__USERNAME__ = "dev"
__BASE_URL__ = "htttp://pantofola.io/"


def search(query):
    imdb_id = query.imdb_id if "imdb_id" in query else ""
    query = "" if "imdb_id" in query else query

    query_url = __BASE_URL__ + __LANGUAGE__ + "/cp/"
    resp = provider.GET(query_url, params={
        "imdbid": imdb_id,
        "search": query,
        "user": __USERNAME__,
        "passkey": __PASS_KEY__,
        "pulsar": "1"
    })
    return resp.json()['results']


def search_episode(episode):
    return ""


def search_movie(movie):
    return search(movie)


# This registers your module for use
provider.register(search, search_movie, search_episode)