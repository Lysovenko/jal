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
Making a face of the application
"""

from tkinter.tix import Tk, Menu, PhotoImage
from tkinter import ttk, Text, StringVar, messagebox
from tkinter.filedialog import askdirectory
from connect import search, dp_get, load_file
from parser import InfoParser
from os.path import expanduser, isdir, join, dirname
from os import makedirs
from threading import Thread, Lock


def autoscroll(sbar, first, last):
    """Hide and show scrollbar as needed."""
    first, last = float(first), float(last)
    if first <= 0 and last >= 1:
        sbar.grid_remove()
    else:
        sbar.grid()
    sbar.set(first, last)


class Config(dict):
    def __init__(self):
        self.path = expanduser("~/.ex_ua_get")
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


class Face:
    def __init__(self, root):
        root.title("EX-UA media loader")
        root.protocol("WM_DELETE_WINDOW", self.on_delete)
        self.root = root
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        self.ufid = []
        self.cfg = Config()
        root.geometry(self.cfg.get("geometry"))
        self.add_control(root)
        pw = ttk.Panedwindow(root, orient="vertical")
        self.pw = pw
        frame = ttk.Frame(pw)
        self.add_tree(frame)
        pw.add(frame)
        frame = ttk.Frame(pw)
        self.add_text(frame)
        pw.add(frame)
        pw.grid(column=0, row=1, columnspan=2, sticky="senw")
        self.pw.sashpos(0, self.cfg.get("sashpos"))
        self.sz = ttk.Sizegrip(root)
        self.sz.grid(column=1, row=2, sticky="se")
        self.status = StringVar()
        st_lab = ttk.Label(root, textvariable=self.status)
        st_lab.grid(column=0, row=2, sticky="we")
        self.add_menu()
        self.locked = False
        self.slock = Lock()
        self.pages = {}
        self.remember = self.cfg.get("remembered", {})
        self.do_remember()
        root.tk.call("wm", "iconphoto", root._w,
                     PhotoImage(file=join(dirname(__file__), "favicon.gif")))

    def do_remember(self):
        for l, t in self.remember.items():
            self.pages[l] = {"entered": False}
            tags = ("page", "bmk")
            if type(t) == tuple:
                t, f = t
                self.pages[l]["folder"] = f
                tags += ("folder",)
            self.tree.insert("", "end", l, text=t, tags=tags)

    def add_control(self, frame):
        self.control = ttk.Frame(frame)
        self.control.grid_columnconfigure(1, weight=1)
        self.control.grid(column=0, row=0, columnspan=2, sticky="ew")
        self.btn = ttk.Button(self.control, command=self.get_url,
                              text="Search", width=8)
        self.btn.grid(column=0, row=0, sticky="w")
        self.entry = ttk.Entry(self.control, width=60)
        self.entry.grid(column=1, row=0, sticky="ew", padx=3)
        self.entry.bind("<KeyPress-Return>", self.get_url)
        self.dirname = StringVar()
        self.dirname.set(self.cfg.get("last-dir", ""))
        self.dirbut = ttk.Button(self.control, command=self.ask_dir,
                                 text="Browse...")
        self.dirbut.grid(column=0, row=1, sticky="ew")
        self.dirlab = ttk.Label(self.control, textvariable=self.dirname)
        self.dirlab.grid(row=1, column=1, sticky="ew")

    def add_tree(self, frame):
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(frame, selectmode="extended")
        self.treef = frame
        self.tree.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=self.tree.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        self.tree["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        hsb = ttk.Scrollbar(
            frame, command=self.tree.xview, orient="horizontal")
        hsb.grid(column=0, row=1, sticky="ew")
        self.tree["xscrollcommand"] = lambda f, l: autoscroll(hsb, f, l)
        self.tree.tag_bind("page", "<Return>", self.enter_page)
        self.tree.tag_bind("page", "<Double-Button-1>", self.enter_page)
        self.tree.tag_bind("page", "<Delete>", self.del_page)
        self.tree.tag_bind("page", "<Insert>", self.remember_pg)
        self.tree.tag_bind("file", "<Return>", self.enter_file)
        self.tree.tag_bind("file", "<Double-Button-1>", self.enter_file)
        self.tree.tag_configure("page", background="gray")
        self.tree.tag_configure("file", foreground="blue", font="Monospace 12")
        self.tree.tag_configure("bmk", foreground="red")
        self.tree.tag_configure("folder", font="Times 14 bold")

    def add_text(self, frame):
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        text = Text(frame, state="disabled", wrap="word",
                    font="Times 14")
        self.text = text
        text.grid(column=0, row=0, sticky="nwes")
        vsb = ttk.Scrollbar(frame, command=self.text.yview, orient="vertical")
        vsb.grid(column=1, row=0, sticky="ns")
        text["yscrollcommand"] = lambda f, l: autoscroll(vsb, f, l)
        self.text_curinfo = None
        text.tag_configure("h1", font="Times 16 bold", relief="raised")

    def add_menu(self):
        top = self.tree.winfo_toplevel()
        top["menu"] = self.menubar = Menu(top)
        self.mfile = Menu(self.menubar)
        self.medit = Menu(self.menubar)
        self.menubar.add_cascade(menu=self.mfile, label="File")
        self.menubar.add_cascade(menu=self.medit, label="Edit")
        self.mfile.add_command(label="Get URL", command=self.get_url)
        self.mfile.add_command(label="Select dir...", command=self.ask_dir)
        self.mfile.add_command(label="Select default folder...",
                               command=self.ask_dir)
        self.medit.add_command(label="Clear",
                               command=self.clear_list)

    def get_url(self, evt=None):
        self.sstatus("Wait...")
        pages = self.pages
        sr = search(self.entry.get())
        for i in sr:
            l = i["link"]
            if l not in pages:
                self.tree.insert("", "end", l, text=i["text"],
                                 tags=("page",))
                pages[l] = {"entered": False}
        self.sstatus("OK")

    def remember_pg(self, evt=None):
        """Switch page remember"""
        iid = self.tree.focus()
        if iid in self.remember:
            self.tree.item(iid, tags=("page",))
            self.remember.pop(iid)
        else:
            self.tree.item(iid, tags=("page", "bmk"))
            self.remember[iid] = self.tree.item(iid)["text"]

    def clear_list(self, evt=None):
        for i in self.pages:
            self.tree.delete(i)
        self.pages.clear()
        del self.ufid[:]
        self.do_remember()

    def ask_dir(self, evt=None):
        if self.locked:
            return
        inidir = self.dirname.get()
        text = None
        if self.text_curinfo in self.remember:
            text = self.remember[self.text_curinfo]
            if type(text) == tuple:
                text, inidir = text
        dname = askdirectory(initialdir=inidir, parent=self.root)
        if type(dname) == str and dname:
            if not isdir(dname):
                if messagebox.askyesno(
                        message="Are you sure you want to create "
                        "a new directory?",
                        icon="question", title="New directory") is False:
                    return
                makedirs(dname)
            if text is not None:
                self.remember[self.text_curinfo] = (text, dname)
            else:
                self.dirname.set(dname)

    def del_page(self, evt=None):
        if type(evt) == str:
            iid = evt
        else:
            iid = self.tree.focus()
            if iid in self.remember:
                if messagebox.askyesno(
                        message="Are you sure you want to "
                        "delete preserved page?",
                        icon="question", title="Install") is False:
                    return
        self.tree.delete(iid)
        self.remember.pop(iid, None)
        page = self.pages.pop(iid)
        if "contains" in page:
            i = 0
            ufids = self.ufid
            while i < len(ufids):
                if ufids[i][3] == iid:
                    ufids.pop(i)
                else:
                    i += 1

    def enter_page(self, evt=None):
        if self.locked:
            return
        self.sstatus("Wait...")
        iid = self.tree.focus()
        if not self.pages[iid]["entered"]:
            self.pages[iid]["entered"] = True
            try:
                files, info = dp_get(iid)
            except:
                self.sstatus("Error")
                return
            if files:
                if info:
                    self.pages[iid]["info"] = InfoParser(info).text
                    self.text_info(iid)
                tids = []
                for u, f in files:
                    tid = self.tree.insert(iid, "end", text=f, tags=("file",))
                    self.ufid.append((u, f, tid, iid))
                    tids.append(tid)
                self.pages[iid]["contains"] = tids
                self.sstatus("OK")
            else:
                self.del_page(iid)
                self.sstatus("Bad item detected and destroyed.")
        else:
            self.text_info(iid)

    def text_info(self, iid):
        if self.text_curinfo != iid:
            self.text_curinfo = iid
            info = self.pages[iid].get("info")
            if not info:
                return
            text = self.text
            text["state"] = "normal"
            text.delete("1.0", "end")
            for i in info:
                text.insert("end", *i)
            text["state"] = "disabled"

    def enter_file(self, evt=None):
        if self.locked:
            return
        self.locked = True
        sel = self.tree.selection()
        t = Thread(target=self.t_enter_file, args=(sel,))
        t.daemon = True
        t.start()

    def t_enter_file(self, sel):
        ufids = []
        for i in self.ufid:
            if i[2] in sel:
                ufids.append(i)
        nfiles = len(ufids)
        sis = self.sstatus
        ddir = self.dirname.get()
        for i, t in enumerate(ufids):
            sst = "%d of %d (%%s) %s" % (i + 1, nfiles, t[1])
            wwp = lambda x: sis(sst % x)
            iid = t[3]
            odir = ddir
            if iid in self.remember:
                rv = self.remember[iid]
                if type(rv) == tuple:
                    odir = rv[1]
            rb = -1
            ra = None
            while rb != ra and ra != 0:
                rb = ra
                ra = load_file(t[0], join(odir, t[1]), wwp)
        self.locked = False
        sis("Done")

    def on_delete(self):
        cfg = self.cfg
        cfg["remembered"] = self.remember
        cfg["last-dir"] = self.dirname.get()
        cfg["geometry"] = self.root.geometry()
        cfg["sashpos"] = self.pw.sashpos(0)
        cfg.save()
        self.root.destroy()

    def sstatus(self, msg):
        self.slock.acquire()
        self.status.set(msg)
        self.slock.release()


def start_face():
    root = Tk()
    f = Face(root)
    root.mainloop()


if __name__ == "__main__":
    start_face()
