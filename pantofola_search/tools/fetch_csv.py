__author__ = 'armanini'

import sys

from bingy import Search
from pantofola_search.tools.pantofola_fetcher import TorrentFetcher
import re


reload(sys)
sys.setdefaultencoding('utf-8')


def main():
    f = open("broken.csv", 'r')
    out = open("broken_fixed.csv", 'w')
    not_found = open("not_found.csv", 'w')
    api = True
    bis = Search()
    myTorrent = TorrentFetcher()
    imdb_re = re.compile(r'(?P<imdb_id>tt\d{7})', flags=re.IGNORECASE + re.MULTILINE)
    for line in f:
        line = line.replace("\n", "")
        line_info = line.split("::")
        movie_title = unicode(line_info[2], errors='ignore')
        clean_title = myTorrent.clean_title(movie_title)
        print "process: ", clean_title
        search_q = clean_title + " site:imdb.com"
        b_r = bis.query(search_q, api, False)
        for u in b_r:
            res = imdb_re.search(u[0])
            if res:
                url = u[0]
                print "Found: ", url
                line += url + "::"
                out.write(line + "\n")
                out.flush()
                print "ij"
                break
            else:
                not_found.write(line + "\n")
                not_found.flush()
                print "Not found"
        if not b_r:
            not_found.write(line + "\n")
            not_found.flush()
            print "Not found"
    out.close()
    not_found.close()
    f.close()


if __name__ == "__main__":
    main()