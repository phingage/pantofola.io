import urllib2, re, difflib
from HTMLParser import HTMLParser
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class AKAImbdParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.get_data = False
        self.in_table = False
        self.in_row = False
        self.in_cols = False
        self.is_original = False
        self.titles = []
        self.foreign_titles = []
        self.original = u""
        self.year = 0
        self.col_n = 0
        self.sup_title = u''
        self.for_title_lang = u''
        self.get_for_title = False

    def get_titles(self):
        if len(self.original) > 0 and len(self.titles) > 0:
            return [self.original, list(set(self.titles)), self.foreign_titles]
        else:
            return [self.sup_title, list(set(self.titles)), self.foreign_titles]

    def handle_starttag(self, tag, attrs):
        if tag == u'meta' and (u'property', u'og:title') in attrs:
            page_title = attrs[1][1]
            year_re = re.search("(?P<title>.*)\((?P<year>\d{4})\)", page_title)
            if year_re:
                self.year = year_re.group("year")
                self.sup_title = year_re.group('title')
            else:
                self.sup_title = page_title
        if tag == u'table' and (u'id', u'akas') in attrs:
            self.in_table = True
        if tag == u'tr' and self.in_table:
            self.in_row = True
        if tag == u'td' and self.in_row:
            self.in_cols = True

    def handle_endtag(self, tag):
        if tag == u'table' and self.in_table:
            self.in_table = False
            self.in_row = False
            self.in_cols = False
        if tag == u'tr' and self.in_row:
            self.in_row = False
            self.in_cols = False
            self.col_n = 0
        if tag == u'td' and self.in_cols:
            self.in_cols = False

    def handle_data(self, data):
        if self.in_cols:
            l_data = data.lower()
            if self.get_data:
                to_send = [data, ""]
                if self.get_for_title:
                    to_send[1] = self.for_title_lang
                    self.foreign_titles.append(to_send)
                    self.get_for_title = False
                if self.is_original:
                    self.original = data
                    self.is_original = False
                else:
                    self.titles.append(data)
                self.get_data = False
            if u"original title" in l_data:
                self.get_data = True
                self.is_original = True
            if u'italy' in l_data or u'france' in l_data or u'spain' in l_data or u'germany' in l_data:
                print "CATCH ", l_data
                if u'italy' in l_data:
                    self.for_title_lang = "ITA"
                if u'germany' in l_data:
                    self.for_title_lang = "GER"
                if u'spain' in l_data:
                    self.for_title_lang = "SPA"
                if u'france' in l_data:
                    self.for_title_lang = "FRE"
                self.get_for_title = True
            if self.col_n == 0:
                self.get_data = True
            self.col_n += 1


class ImdbFetcher(object):
    """description of class"""

    def __init__(self):
        self.aka_url = u"http://www.imdb.com/title/%s/releaseinfo"
        self.search_url = u"http://m.imdb.com/find?q=%s"
        self.title_re = re.compile(r'href="/title/(?P<imdb_id>tt\d{7})/', flags=re.IGNORECASE + re.MULTILINE)
        self.aka_parser = AKAImbdParser()

    def query_a_title(self, title):
        web_ready_title = urllib2.quote(title.encode('utf-8'))
        query_url = self.search_url % web_ready_title
        query_resp = urllib2.urlopen(query_url)
        reps_html = query_resp.read()
        res = self.title_re.search(reps_html)
        if res:
            imdb_id = res.group('imdb_id')
            return imdb_id
        else:
            return None

    def compute_score(self, title, score_titles):
        max_ratio = 0
        for title_n in score_titles:
            seq = difflib.SequenceMatcher(a=title.lower(), b=title_n.lower())
            ratio = seq.ratio()
            if max_ratio < ratio:
                max_ratio = ratio
        return max_ratio

    def query_movie_info(self, imdb_id, title):
        self.aka_parser.__init__()
        titles = self.get_titles(imdb_id)
        max_ratio = 0
        if titles[1]:
            score_titles = titles[1][1]
            score_titles.append(titles[1][0])
            max_ratio = self.compute_score(title, score_titles)
        else:
            max_ratio = self.compute_score(title, self.aka_parser.sup_title)
            titles[1].append(self.aka_parser.sup_title)
        return [imdb_id, titles[0], max_ratio, titles[1]]

    def get_titles(self, imbd_id):
        query_url = self.aka_url % imbd_id
        try:
            query_resp = urllib2.urlopen(query_url)
            reps_html = query_resp.read()
            self.aka_parser.feed(reps_html)
            titles = self.aka_parser.get_titles()
            year = self.aka_parser.year
            return [year, titles]
        except:
            return ["0", ["", [], []]]


if __name__ == "__main__":
    imbd = ImdbFetcher()
    print imbd.query_movie_info(u"tt0088763", u"ritorno al futuro")

    
                



