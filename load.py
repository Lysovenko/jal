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
Loader
"""

from os.path import basename
from threading import Thread, Lock
from time import time, mktime, strptime, timezone
import os.path as osp
from urllib.error import HTTPError, URLError
from urllib.request import urlopen, Request


class Loader:
    def __init__(self, sstatus):
        self.sstatus = sstatus
        self.qlock = Lock()
        self.running = False
        self.queue = []

    def add_file(self, url, fname):
        self.qlock.acquire()
        self.queue.append((url, fname))
        if (not self.running) and self.queue:
            t = Thread(target=self.t_load)
            t.daemon = True
            t.start()
        self.qlock.release()

    def t_load(self):
        "loader thread"
        sis = self.sstatus
        self.qlock.acquire()
        self.running = True
        self.qlock.release()
        while True:
            self.qlock.acquire()
            if self.queue:
                uft = self.queue.pop(0)
            else:
                self.running = False
                self.qlock.release()
                break
            self.qlock.release()
            sst = _("%%s\t%s (%%d remains)") % \
                basename(uft[1]).replace("%", "%%")
            wwp = lambda x, y=self.queue: sis(sst % (x, len(y)))
            rb = -1
            ra = None
            while rb != ra and ra != 0:
                rb = ra
                ra = load_file(uft[0], uft[1], wwp)
        sis(_("Done"))


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
    wwp(_("Connecting..."))
    lwt = time()
    try:
        hdata = urlopen(req)
        cont_len = int(hdata.info().get("Content-Length", 0))
        m_time = mktime(strptime(hdata.info().get("Last-Modified"),
                                 "%a, %d %b %Y %H:%M:%S %Z")) - timezone
    except (HTTPError,) as err:
        if err.code == 416:
            wwp(_("Nothing to do"))
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
                wwp("%05.2f%% %sETA" %
                    ((written + res_len) / (cont_len + res_len) * 100, etime))
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
    if nbytes == 0:
        return "--:--:--"
    seconds = int(elapsed / nbytes * ebytes)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 99:
        return "--:--:--"
    return "%02d:%02d:%02d" % (hours, minutes, seconds)
