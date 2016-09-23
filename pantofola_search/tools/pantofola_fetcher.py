# -*- coding: utf-8 -*-
import re, difflib, string

import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class TorrentFetcher(object):
    def __init__(self):
        self.reverse_language = {'SPA': 'SPA',
                                 'ESP': 'SPA',
                                 "GER": 'GER',
                                 'ITA': 'ITA',
                                 'FRA': 'FRA',
                                 "FRE": "FRA"}
        self.italian_re = ur"\bitalian\b|\bita\b"
        self.french_re = ur"\bfrench\b|\bfre\b|\bfrançais\b"
        self.german_re = ur"\bgerman\b|\bger\b"
        self.spanish_re = ur"\bspanish\b|\bspa\b|\bespañol\b"

        self.lang_re = u'|'.join([self.italian_re, self.french_re, self.german_re, self.spanish_re])

        self.video_format = [u"720p", u"1080p", u"480p", u'576i', u'microhd', u'360p', u'540p', u'fullhd', u'hd1080',
                             u'4k', u'576p']

        self.video_codec = [u"divx", u"xvid", u"x264", u"x265", u'mvc', u'h264']

        self.video_source = [u"bdrip", u"bluray", ur"\bcam\b", u"brrip", ur"web\sdl", u"webdl", u"webrip",
                             u"dvdrip", u'dvdr', u'bdremux', u'tvsatrip', u'camrip', u'bdrp', u'dttrip',
                             u"webrip", u"tvrip", u"hdrip", u'dvd9', ur'blu\sray', ur'\bts\b', u'telesync',
                             u'dvd5', u'hdtv', ur'bd\srip', u'dbrip', u'vhsrip', u'hdcam', u'ntsc', u'dvdscr', u'3d',
                             u'screener']

        self.audio_source = [ur"\bmd\b", ur"\bld\b", ur"\bdd\b", ur"\baac\b", u"dts", u"dsp", u"dsp2", u"mp3",
                             u"resync", u"ac3", ur'dd5\s1']

        self.remove_words = [ur"\[.*?\]|^\(.*?\)", u'HD2DVDR', u"italian", ur"\bita\b", u"xvid trl", ur"\bavi\b",
                             ur"\beng\b",
                             u"french", ur"\bfre\b", u"mircrew", u'subforced', u'nforelease', u'mp4', ur"\bvfq\b",
                             u"german", ur"\bger\b", u"spanish", ur"\bspa\b", u'mkv', ur'\biso\b', ur'\btrl\b', u'tsrip'
                                                                                                                ur'\bsrt\b',
                             ur'\bsubs\b', ur'\bdvd\b', ur'\brip\b', u'tntvillage', ur'\bpal\b', ur'\br5\b'
                                                                                                 ur'\bsubita\b',
                             ur'\bhd\b', ur'\bbd\b', ur'\bsubbed\b', ur'\bstv\b', u'~', u'bdrp', u'dttrip',
                             u'dbrip', u'bd50', ur'\brepack\b', ur'\bsubtitles\b', u'readnfo', ur'\br6\b', u'satrip',
                             ur'\bhq\b',
                             u'dvdscr', u'trackersurfer', u'hd2', u'msvcd', ur'\br6\b', ur'\bdl\b', ur'\vid\b',
                             u'dvdscrenner',
                             ur'\bscrenner\b', ur'\brerip\b', ur'\bunrated\b', ur'\bspecial\sedition\b', ur'\b2dvd\b',
                             ur'\benglish\b',
                             ur'\bdisc1\b', ur'\bdisc2\b', ur'\bdisc3\b', ur'\[tntvil', ur'\bbr\b', ur'\bcvcd\b',
                             u'pdtv',
                             ur'\bdfr\b', ur'\bvid\b', u'1cd', u'2cd', ur'\bgtm\b', ur'\bws\b', ur'\bpsh\b', u'dvds',
                             u'reencode', ur'\bvf\b', ur'\bvhs\b', u'multisub', u'v0h1', u'screnner', ur'\buncut\b',
                             u'español', u'français']

        self.sanitized_chart = u".-_{}#+"
        self.sanitized_table = u' ' * len(self.sanitized_chart)
        self.trans_table = string.maketrans(self.sanitized_chart, u' ' * len(self.sanitized_chart))

        self.to_remove_rex = u'|'.join(
            self.video_format + self.video_codec + self.audio_source + self.video_source + self.remove_words)

        self.first_occurrence_rex = u'|'.join(
            self.video_format + self.video_codec + self.audio_source + self.video_source + [ur"\[.*?\]|^\(.*?\)"])

        self.video_source_tags = u'|'.join(self.video_source)
        self.video_format_tags = u'|'.join(self.video_format)
        self.video_codec_tags = u'|'.join(self.video_codec)
        self.audio_source_tags = u'|'.join(self.audio_source)

        self.first_rex = re.compile(self.first_occurrence_rex, flags=re.IGNORECASE)
        self.remove_rex = re.compile(self.to_remove_rex, flags=re.IGNORECASE)
        self.video_source_rex = re.compile(self.video_source_tags, flags=re.IGNORECASE)
        self.video_format_rex = re.compile(self.video_format_tags, flags=re.IGNORECASE)
        self.video_codec_rex = re.compile(self.video_codec_tags, flags=re.IGNORECASE)
        self.audio_source_rex = re.compile(self.audio_source_tags, flags=re.IGNORECASE)

    def sanitize_title(self, title):
        tabin = [ord(char) for char in self.sanitized_chart]
        translate_table = dict(zip(tabin, self.sanitized_table))
        title_sanitized = title.translate(translate_table)
        return title_sanitized.lower()

    def check_good_lenguage(self, title_sanitized):
        result = re.search(self.lang_re, title_sanitized)
        if result:
            lang_tag = result.group(0)[:3].upper()
            return self.reverse_language[lang_tag]
        else:
            return None

    def extract_tag(self, title_sanitized):
        tags = [u"", u"", u"", u""]
        # #CHECK TAG
        video_source_tag = self.video_source_rex.search(title_sanitized)
        video_format_tag = self.video_format_rex.search(title_sanitized)
        video_codec_tag = self.video_codec_rex.search(title_sanitized)
        audio_source_tag = self.audio_source_rex.search(title_sanitized)
        if video_source_tag:
            tags[0] = video_source_tag.group(0)
        if video_format_tag:
            tags[1] = video_format_tag.group(0)
        if video_codec_tag:
            tags[2] = video_codec_tag.group(0)
        if audio_source_tag:
            tags[3] = audio_source_tag.group(0)
        return tags

    def clean_title(self, title_sanitized):
        s_title = self.sanitize_title(title_sanitized)

        while 1:
            clean_title = re.sub(ur"^\[.*?\]|^\(.*?\)", '', str(s_title.lstrip()))
            if clean_title == s_title:
                break
            else:
                s_title = clean_title

        clean_title = clean_title.strip()
        possible_good_title = clean_title
        print "Clean Title ", possible_good_title
        first_index = 0
        fist_occurrence = self.first_rex.search(clean_title, re.UNICODE)
        if fist_occurrence:
            first_index = fist_occurrence.start()
        if first_index > 0:
            cut_title = clean_title[:first_index]
        else:
            cut_title = clean_title
        print "Cut title: ", cut_title
        return_title = self.remove_rex.sub("", unicode(cut_title), re.UNICODE)
        # #add ' to 1 words
        return_title = re.sub(ur"\bl\s\b", "l'", return_title)
        return_title = re.sub(ur"\bd\s\b", "d'", return_title)
        return_title = re.sub(ur"\bc\s\b", "c'", return_title)
        ##final clean
        return_title = re.sub(ur"\(|\)", "", return_title)
        print "Return title: ", return_title
        return return_title.strip()


if __name__ == '__main__':
    start_s = ur"la pirámide  español pdtv"
    myTorrent = TorrentFetcher()
    print myTorrent.to_remove_rex
    myTorrent.clean_title(start_s)
    # from imdb_fetcher import ImdbFetcher
    #
    # my_imdb = ImdbFetcher()
    # filename = "../../data/test.txt"
    # data_file = open(filename, 'r')
    # myTorrent = TorrentFetcher()
    # processd = []
    # failed = []
    # for line in data_file:
    # data_line = line.split("|")
    #     # fetch movies only
    #     if data_line[2] == u"Movies":
    #         movie_title = data_line[1]
    #         # replace . with space
    #         title_sanitized = myTorrent.sanitize_title(movie_title)
    #         result = myTorrent.check_good_lenguage(title_sanitized)
    #         if result:
    #             lang_tag = result
    #             magnet_link = data_line[0]
    #             kick_ass_link = data_line[3]
    #             tor_cache_link = data_line[4]
    #             tags = myTorrent.extract_tag(title_sanitized)
    #             clean_title = myTorrent.clean_title(title_sanitized)
    #             print clean_title
    #             imdb_id = my_imdb.query_a_title(clean_title)
    #             if imdb_id:
    #                 movie_info = my_imdb.query_movie_info(imdb_id, clean_title)
    #                 print movie_info, tags, lang_tag
    #             else:
    #                 print "not_found"
