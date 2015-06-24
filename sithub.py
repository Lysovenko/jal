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

import ex_ua


_SIT_MDLS = {"ex-ua": ex_ua}


def get_sites():
    return [("ex-ua", "EX-UA"), ("youtube", "YouTube")]


def web_search(what, where):
    result = []
    for i in where:
        if i in _SIT_MDLS:
            result += _SIT_MDLS[i].web_search(what)
    return result


def get_datapage(site, page):
    if site in _SIT_MDLS:
        return _SIT_MDLS[site].get_datapage(page)
    else:
        raise KeyError("Wrong site name")
