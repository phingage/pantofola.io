__author__ = 'armanini'
import httplib, requests, re

from urlparse import urlparse


class KickAssFetcher(object):
    def __init__(self):
        self.search_url = "http://kickass.to/usearch/"
        self.title_re = re.compile(r'(?P<imdb_id>tt\d{7})', flags=re.IGNORECASE + re.MULTILINE)

    def search(self, torrent_hash):
        url = self.search_url + torrent_hash
        print "Start search for: ", url
        r = requests.get(url)

        if len(r.history) < 0 or r.history[-1].status_code != 302:
            print "No History ", r.history
            return None

        res = self.title_re.findall(r.text)
        print res
        if res:
            print "Found: ", res[-1]
            return res[-1]
        else:
            print "Imdb Not found!"
            return None

    def get_status_code(self, url):
        url_part = urlparse(url)

        try:
            conn = httplib.HTTPConnection(url_part.netloc)
            conn.request("HEAD", url_part.path)
            return conn.getresponse().status
        except:
            return None


def main():
    kParse = KickAssFetcher()
    kParse.search("252DDC4D3EF6E7EE393CD842239ACEB86BF7A546")


if __name__ == "__main__":
    main()