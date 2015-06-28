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
"""
YouTube data parser
"""
from html.parser import HTMLParser
from sys import hexversion
from os import popen


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
        self.feed(data)
        self.close()

    def handle_starttag(self, tag, attrs):
        dattrs = dict(attrs)
        if tag == "a" and \
           "yt-uix-tile-link" in dattrs.get("class", "").split():
            curdata = {}
            curdata["title"] = dattrs["title"]
            curdata["page"] = dattrs["href"]
            curdata["site"] = "youtube"
            self.found.append(curdata)


def parse_dpage(url):
    furl = popen("youtube-dl -gf5 '%s'" % url, "r").read()
    title = popen("youtube-dl --get-title '%s'" % url, "r").read()
    fname = title.translate({34: 95, 47: 95}).strip() + '.flv'
    res = [(furl, fname)]
    info = [(popen("youtube-dl --get-description '%s'" % url, "r").read(), ())]
    return res, info
