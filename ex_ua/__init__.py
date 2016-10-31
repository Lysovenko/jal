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
EX-UA data treatment
"""

from urllib.request import urlopen, Request
from urllib.parse import urlencode
from .parser import SearchParser, parse_dpage, InfoParser, CatalogParser
from hashlib import md5


def web_search(what):
    o = urlopen("http://ex.ua/search?%s" %
                urlencode([("s", what), ("per", 100)]))
    sp = SearchParser(o.read().decode())
    del o
    if sp.found:
        for i in sp.found:
            md5o = md5("/".join((i["site"], i["page"])).encode("utf8"))
            i["hash"] = md5o.hexdigest()
        return list(sp.found)
    return []


def get_datapage(page):
    r = Request("http://www.ex.ua" + page)
    o = urlopen(r)
    html_text = o.read().decode()
    o.close()
    files, info = parse_dpage(html_text)
    if info:
        info = InfoParser(info).text
    if files:
        return files, info, "Files"
    cat_par = CatalogParser(html_text)
    found = list(cat_par.found)
    for i in found:
            md5o = md5("/".join((i["site"], i["page"])).encode("utf8"))
            i["hash"] = md5o.hexdigest()
    return found, list(cat_par.text), "Catalog"
