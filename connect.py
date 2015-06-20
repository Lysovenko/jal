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
Internet connections
"""

from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from parser import SearchParser, parse_dpage
import os.path as osp
from time import time, mktime, strptime, timezone
from hashlib import md5


def web_search(what):
    r = Request("http://ex.ua/search?%s" % urlencode([("s", what),
                                                      ("per", 100)]))
    o = urlopen(r)
    sp = SearchParser(o.read().decode())
    del o
    if sp.found:
        for i in sp.found:
            md5o = md5("/".join((i["site"], i["page"])).encode("utf8"))
            i["hash"] = md5o.hexdigest()
        return sp.found


def dp_get(site, page):
    if site == "ex-ua":
        r = Request("http://www.ex.ua" + page)
    else:
        raise KeyError("Wrong site name")
    o = urlopen(r)
    return parse_dpage(o.read().decode())


def load_file(url, outfile, wwp):
    req = Request(url)
    if osp.isfile(outfile):
        res_len = osp.getsize(outfile)
    else:
        res_len = 0
    open_mode = "wb"
    if res_len > 0:
        req.add_header("Range", "bytes=%d-" % res_len)
        open_mode = "ab"
    wwp("Connecting...")
    lwt = time()
    try:
        hdata = urlopen(req)
        cont_len = int(hdata.info().get("Content-Length", 0))
        m_time = mktime(strptime(hdata.info().get("Last-Modified"),
                                 "%a, %d %b %Y %H:%M:%S %Z")) - timezone
    except (HTTPError,) as err:
        if err.code == 416:
            wwp("Nothing to do")
            return
        if err.code < 500 or err.code >= 600:
            raise
    written = 0
    if cont_len == 0:
        return
    start = time()
    block_size = min(1024, cont_len)
    with open(outfile, open_mode) as fo:
        while written < cont_len:
            before = time()
            d_bl = hdata.read(block_size)
            written += len(d_bl)
            if len(d_bl) == 0:
                break
            fo.write(d_bl)
            after = time()
            block_size = best_block_size(after-before, len(d_bl))
            etime = calc_estimated_time(
                after - before, len(d_bl), cont_len - written)
            if after - lwt >= 1:
                wwp("%0.2f%% %sETA" % (written/cont_len*100, etime))
                lwt = after
    osp.os.utime(outfile, (time(), m_time))
    return cont_len - written


def best_block_size(elapsed_time, nbytes):
    new_min = max(nbytes / 2.0, 1.0)
    new_max = min(max(nbytes * 2.0, 1.0), 4194304)
    if elapsed_time < 0.001:
        return int(new_max)
    rate = nbytes / elapsed_time
    if rate > new_max:
        return int(new_max)
    if rate < new_min:
        return int(new_min)
    return int(rate)


def calc_estimated_time(elapsed, nbytes, ebytes):
    seconds = int(elapsed / nbytes * ebytes)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    tparts = [hours, minutes, seconds]
    while tparts[0] == 0 and len(tparts) > 1:
        tparts.pop(0)
    return ':'.join({'%02d' % i for i in tparts})
