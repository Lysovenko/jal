# Copyright 2015 Serhiy Lysovenko
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from html.parser import HTMLParser
from sys import hexversion


class SearchParser(HTMLParser):
    "parses  html file"
    def __init__(self, data):
        di = {}
        if hexversion >= 0x030200f0:
            di["strict"] = False
        HTMLParser.__init__(self, **di)
        self.found = []
        self.is_topen = False
        self.is_aopen = False
        self.curdata = {}
        self.feed(data)
        self.close()

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == "table":
            if dattrs.get("class") == "panel":
                self.is_topen = True
        if self.is_topen:
            if tag == "a":
                href = dattrs.get("href", "")
                if href.startswith("/") and href[1:].isdigit():
                    self.curdata["page"] = href
                    self.curdata["site"] = "ex-ua"
                    self.is_aopen = True

    def handle_endtag(self, tag):
        if tag == "table":
            self.is_topen = False
        if tag == "td":
            if self.curdata:
                self.curdata["title"] = self.curdata.get("title", "No title")
                self.found.append(self.curdata)
                self.curdata = {}
        if tag == "a":
            self.is_aopen = False

    def handle_data(self, data):
        if self.is_aopen:
            try:
                self.curdata["title"] += data
            except KeyError:
                self.curdata["title"] = data


class CatalogParser(HTMLParser):
    "parses  Ex-ua catalog"
    def __init__(self, data):
        di = {}
        if hexversion >= 0x030200f0:
            di["strict"] = False
        HTMLParser.__init__(self, **di)
        self.text = []
        self.curtags = []
        self.found = []
        self.is_topen = False
        self.is_aopen = False
        self.parse_info = False
        self.curdata = {}
        self.feed(data)
        self.close()

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if self.parse_info:
            if tag == "h1":
                self.curtags.append(tag)
            if tag == "p":
                self.text.append(("\n    ", ()))
            if tag == "br":
                self.text.append(("\n", ()))
        if tag == "td" and dattrs.get("valign") == "top":
            self.parse_info = True
        if tag == "table":
            if dattrs.get("class") == "include_0":
                self.is_topen = True
        if self.is_topen:
            if tag == "a":
                href = dattrs.get("href", "")
                if "?" in href:
                    href = href[:href.find("?")]
                if href.startswith("/") and href[1:].isdigit():
                    self.curdata["page"] = href
                    self.curdata["site"] = "ex-ua"
                    self.is_aopen = True

    def handle_endtag(self, tag):
        if self.curtags and tag == self.curtags[-1] and self.parse_info:
            self.curtags.pop(-1)
        if tag == "table":
            self.is_topen = False
        if tag == "td":
            self.parse_info = False
            if self.curdata:
                self.curdata["title"] = self.curdata.get("title", "No title")
                self.found.append(self.curdata)
                self.curdata = {}
        if tag == "a":
            self.is_aopen = False

    def handle_data(self, data):
        if self.parse_info:
            self.text.append((" ".join(data.split()), tuple(self.curtags)))
        if self.is_aopen:
            try:
                self.curdata["title"] += data
            except KeyError:
                self.curdata["title"] = data


_MEDIA_TYPES = {"video": "flv", "audio": "mp3"}


def parse_dpage(text):
    pos = text.find("player_list")
    if pos < 0:
        return None, None
    st = text.find("'", pos)
    if st < 0:
        return None, None
    st += 1
    en = text.find("'", st)
    arr = eval("["+text[st:en]+"]")
    res = []
    for row in text.split("<tr>"):
        if "play_index(" in row and "title=" in row:
            tp = row.find("title=")
            tp += 7
            te = row.find("'", tp)
            fname = row[tp:te]
            fname = fname[:fname.rfind(".")]
            tp = row.find("play_index(")
            tp += 11
            te = row.find(")", tp)
            try:
                ind = int(row[tp:te])
            except:
                continue
            fname = fname.replace("&#39;", "'").replace("&amp;", "&")
            i = arr[ind]
            fname += "." + _MEDIA_TYPES.get(i["type"], i["type"])
            res.append((i["url"], fname))
    st = text.find("<td valign=top>")
    if st > 0:
        st += 15
        en = text.find("</td>", st)
        info = text[st:en]
    else:
        info = None
    return res, info


class InfoParser(HTMLParser):
    "parses  html file"
    def __init__(self, data):
        di = {}
        if hexversion >= 0x030200f0:
            di["strict"] = False
        HTMLParser.__init__(self, **di)
        self.text = []
        self.is_topen = False
        self.is_aopen = False
        self.curtags = []
        self.feed("\n".join(data.splitlines()))
        self.close()

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == "h1":
            self.curtags.append(tag)
        if tag == "p":
            self.text.append(("\n    ", ()))
        if tag == "br":
            self.text.append(("\n", ()))

    def handle_endtag(self, tag):
        if self.curtags and tag == self.curtags[-1]:
            self.curtags.pop(-1)

    def handle_data(self, data):
        self.text.append((" ".join(data.split()), tuple(self.curtags)))
