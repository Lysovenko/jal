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
from connect import load_file

class Loader:
    def __init__(self, sstatus):
        self.sstatus = sstatus
        self.qlock = Lock()
        self.running = False
        self.queue = []

    def add_file(self, url, fname):
        self.qlock.acquire()
        self.queue.append((url, fname))
        if not self.running and self.queue:
            t = Thread(target=self.t_load)
            t.daemon = True
            t.start()
        self.qlock.release()

    def t_load(self):
        sis = self.sstatus
        self.qlock.acquire()
        self.running = True
        self.qlock.release()
        while True:
            self.qlock.acquire()
            if self.queue:
                uft = self.queue.pop(0)
                leave = len(self.queue)
            else:
                self.running = False
                self.qlock.release()
                break
            self.qlock.release()
            sst = "%%s\t%s (%d leaves)" % (basename(uft[1]), leave)
            wwp = lambda x: sis(sst % x)
            rb = -1
            ra = None
            while rb != ra and ra != 0:
                rb = ra
                ra = load_file(uft[0], uft[1], wwp)
        sis(_("Done"))

