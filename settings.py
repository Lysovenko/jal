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
Deal with application's settings
"""

from os.path import expanduser


class Config(dict):
    def __init__(self):
        self.path = expanduser("~/.jml")
        cfgl = []
        try:
            with open(self.path) as fp:
                for line in iter(fp.readline, ""):
                    if not line.isspace():
                        nam, val = line.strip().split(": ", 1)
                        cfgl.append((nam, eval(val)))
        except:
            pass
        dict.__init__(self, cfgl)

    def save(self):
        with open(self.path, "w") as fp:
            for n, v in self.items():
                fp.write("%s: %s\n" % (n, repr(v)))
