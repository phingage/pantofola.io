import urllib2
import gzip
from io import BytesIO

from bcode import bdecode


def get_torrent_size(data):
    if not data:
        return 0
    t_data = bdecode(data)
    t_size = 0
    if 'files' in t_data['info']:
        files = t_data['info']['files']
        for f in files:
            t_size += int(f['length'])
    else:
        t_size += int(t_data['info']['length'])
    return t_size


def get_torrent_metadata_from_url(url):

    try:
        res = urllib2.urlopen(url)
        if res.info().get('Content-Encoding') == 'gzip':
            buf = BytesIO( res.read())
            f = gzip.GzipFile(fileobj=buf)
            data = f.read()

        return data
    except:
        return False

def get_torrent_size_from_url(url):
    return get_torrent_size(get_torrent_metadata_from_url(url))

if __name__ == "__main__":

    url = "http://torcache.net/torrent/3BFE7B44464B1B4E1CE1FD97EA3906535176D8EF.torrent"
    print get_torrent_size(get_torrent_metadata_from_url(url))