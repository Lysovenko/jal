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
Sites hub
"""

import connect as con
from parser import InfoParser


def get_sites():
    return [("ex-ua", _("ex-ua")), ("kinogo", _("KinoGo"))]


def web_search(what, where):
    return con.web_search(what)


def get_datapage(site, page):
    files, info = con.dp_get(site, page)
    if info:
        info = InfoParser(info).text
    return files, info
