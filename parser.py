from html.parser import HTMLParser
from html import escape
from sys import hexversion


class SearchParser(HTMLParser):
    "parses  html file"
    def __init__(self, data):
        di = {}
        if hexversion >= 0x030200f0:
            di['strict'] = False
        HTMLParser.__init__(self, **di)
        self.found=[]
        self.is_topen = False
        self.is_aopen = False
        self.curdata = {}
        self.feed(data)
        self.close()

    def handle_starttag(self, tag, attrs):
        dattrs=dict(attrs)
        if tag == 'table':
            if dattrs.get('class') == 'panel':
                self.is_topen = True
        if self.is_topen:
            if tag == 'a':
                href=dattrs.get('href','')
                if href.startswith('/') and href[1:].isdigit():
                    self.curdata['link'] = href
                    self.is_aopen = True
        pass

    def handle_endtag(self, tag):
        if tag == 'table':
            self.is_topen = False
        if tag == 'td':
            if self.curdata:
                self.found.append(self.curdata)
                self.curdata = {}
        if tag == 'a':
            self.is_aopen = False
    def handle_data(self, data):
        if self.is_aopen:
            try:
                self.curdata['text'] += data
            except KeyError:
                self.curdata['text'] = data
        pass


class GoogleParser(HTMLParser):
    "parses Gogle search result"
    def __init__(self, data):
        di = {}
        if hexversion >= 0x030200f0:
            di['strict'] = False
        HTMLParser.__init__(self, **di)
        self.found=[]
        self.is_topen = False
        self.is_aopen = False
        self.curdata = {}
        self.feed(data)
        self.close()

    def handle_starttag(self, tag, attrs):
        dattrs=dict(attrs)
        if self.is_topen:
            if tag == 'a':
                href=dattrs.get('href','')
                if href.startswith('http://www.ex.ua/') and href[17:].isdigit():
                    self.curdata['link'] = href[16:]
                    self.is_aopen = True
        if tag == 'h3':
            if dattrs.get('class') == 'r':
                self.is_topen = True

    def handle_endtag(self, tag):
        if tag == 'h3':
            self.is_topen = False
            if self.curdata:
                self.found.append(self.curdata)
                self.curdata = {}
        if tag == 'a':
            self.is_aopen = False

    def handle_data(self, data):
        if self.is_aopen:
            try:
                self.curdata['text'] += data
            except KeyError:
                self.curdata['text'] = data


_MEDIA_TYPES = {'video': 'flv', 'audio': 'mp3'}


def parse_dpage(text):
    pos = text.find("player_list")
    if pos < 0:
        return None, None
    st = text.find("'", pos)
    if st < 0:
        return None, None
    st += 1
    en = text.find("'", st)
    arr = eval('['+text[st:en]+']')
    res = []
    for row in text.split("<tr>"):
        if "play_index(" in row and "title=" in row:
            tp = row.find('title=')
            tp += 7
            te = row.find("'", tp)
            fname = row[tp:te]
            fname = fname[:fname.rfind('.')]
            tp = row.find('play_index(')
            tp += 11
            te = row.find(')',tp)
            try:
                ind=int(row[tp:te])
            except:
                continue
            fname = fname.replace('&#39;', "'").replace('&amp;', '&')
            i = arr[ind]
            fname += '.' + _MEDIA_TYPES.get(i["type"], i["type"])
            res.append((i["url"], fname ))
    st = text.find('<td valign=top>')
    if st > 0:
        st += 15
        en = text.find('</td>', st)
        info = text[st:en]
    else:
        info = None
    return res, info


class InfoParser(HTMLParser):
    "parses  html file"
    def __init__(self, data):
        di = {}
        if hexversion >= 0x030200f0:
            di['strict'] = False
        HTMLParser.__init__(self, **di)
        self.text = []
        self.is_topen = False
        self.is_aopen = False
        self.curtags = []
        self.feed('\n'.join(data.splitlines()))
        self.close()

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == 'h1':
            self.curtags.append(tag)
        if tag == 'p':
            self.text.append(('\n    ', ()))
        if tag == 'br':
            self.text.append(('\n', ()))

    def handle_endtag(self, tag):
        if self.curtags and tag == self.curtags[-1]:
            self.curtags.pop(-1)

    def handle_data(self, data):
        self.text.append((' '.join(data.split()), tuple(self.curtags)))
