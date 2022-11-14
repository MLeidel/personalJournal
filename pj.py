'''
code file: pj.py
Personal Journal
'''
from tkinter import *
from tkinter.ttk import *  # defaults all widgets as ttk
from tkinter import scrolledtext
import sqlite3
import configparser
from time import strftime
# import time
import os
import subprocess
import webbrowser
from tkinter.font import Font
from tkinter import messagebox
from autocorrect import Speller
from tkcalendar import *
from ttkthemes import ThemedTk  # ttkthemes is applied to all widgets
import pysftp

class Application(Frame):
    ''' main class docstring '''
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.pack(fill=BOTH, expand=True, padx=4, pady=4)
        # If .pj_ftp.cfg exists then download the
        # pjourn.db database from cloud
        # otherwise will just use local copy of pjourn.db
        if os.path.exists(".pj_ftp.cfg"):
            myftp_download(".pj_ftp.cfg")

        config = configparser.RawConfigParser()
        config.read(".pj.cfg")
        self.fname = config.get('Main', 'fontname')  # MUST be set in .pj.cfg file
        self.fsize = config.get('Main', 'fontsize')  # MUST be set in .pj.cfg file
        self.tedit = config.get('Main', 'editor')    # MUST be set in .pj.cfg file
        self.mac1 = config.get('Main', 'mac1')       # MUST be set in .pj.cfg file
        self.mac2 = config.get('Main', 'mac2')       # MUST be set in .pj.cfg file
        self.mac3 = config.get('Main', 'mac3')       # MUST be set in .pj.cfg file

        self.create_widgets()
        self.spell = Speller(lang='en')


    def create_widgets(self):
        ''' creates GUI for app '''

        myfont = Font(family=self.fname, weight='normal', size=self.fsize)
        boldfont = Font(weight="bold", family='Arial')
        # expand widget to fill the grid
        self.columnconfigure(1, weight=1)
        # self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # customize widget style when using ttk...
        style = Style()
        style.configure("TButton", width=10, font=boldfont) # global

        self.cal = Calendar(self, selectmode="day",
                            year=int(strftime('%Y')),
                            month=int(strftime('%m')),
                            day=int(strftime('%d')),
                            width=400,
                            cursor="hand1",
                            date_pattern='yyyy-mm-dd')
        self.cal.grid(row=1, column=1, sticky='we', pady=5, padx=5)

        self.text_area = scrolledtext.ScrolledText(self,
                                                   wrap=WORD,
                                                   width=40,
                                                   height=12,
                                                   tabs=(myfont.measure(' ' * 4),),
                                                   undo=True,
                                                   padx=5,
                                                   pady=5,
                                                   font=myfont)
        self.text_area.grid(row=2, column=1, sticky='nsew', pady=5, padx=5)

        frm = Frame(self, height=50)
        frm.grid(row=3, column=1)

        self.btn_save = Button(frm, text="Save", command=self.save_entry)
        self.btn_save.grid(row=1, column=1, pady=5, padx=10)
        btn_print = Button(frm, text="List", command=self.list_all)
        btn_print.grid(row=1, column=2, pady=5, padx=10)
        btn_close = Button(frm, text="Close", command=self.exit_program)
        btn_close.grid(row=1, column=3, pady=5, padx=10)

        root.bind("<<CalendarSelected>>", self.calselected)
        root.bind('<Control-s>', self.save_entry)
        root.bind('<Control-q>', self.exit_program)
        root.bind('<Escape>', exit)
        self.text_area.bind('<Alt-s>', self.spellcorrect)
        self.text_area.bind('<Control-t>', self.insert_time)
        self.text_area.bind('<Control-Key-1>', self.insert_macro)
        self.text_area.bind('<Control-Key-2>', self.insert_macro)
        self.text_area.bind('<Control-Key-3>', self.insert_macro)

        # BEGIN MENU
        menubar = Menu(root)
        mn_file = Menu(menubar, tearoff=0)
        mn_file.add_command(label="Save", command=self.nm_file_save, accelerator="Ctrl-s", underline=1)
        mn_file.add_command(label="List Year", command=self.list_all)
        mn_file.add_separator()
        mn_file.add_command(label="Exit", command=self.nm_file_exit, accelerator="Ctrl-q")
        menubar.add_cascade(label="File", menu=mn_file)
        mn_edit = Menu(menubar, tearoff=0)
        mn_edit.add_command(label="Undo", command=self.mn_edit_undo, accelerator="Ctrl-z")
        mn_edit.add_command(label="Redo", command=self.mn_edit_redo, accelerator="Ctrl-y")
        mn_edit.add_command(label="Select All", command=self.mn_edit_selall, accelerator="Ctrl-a")
        submenu = Menu(mn_edit, tearoff=False)
        submenu.add_command(label="Copy", command=self.mn_edit_copy, accelerator="Ctrl-c")
        submenu.add_command(label="Paste", command=self.mn_edit_paste, accelerator="Ctrl-v")
        mn_edit.add_cascade(label="Clipboard", menu=submenu, underline=2)
        mn_edit.add_command(label="Macro 1", command=self.mn_edit_mac1, accelerator="Ctrl-1")
        mn_edit.add_command(label="Macro 2", command=self.mn_edit_mac2, accelerator="Ctrl-2")
        mn_edit.add_command(label="Macro 3", command=self.mn_edit_mac3, accelerator="Ctrl-3")
        menubar.add_cascade(label="Edit", menu=mn_edit)
        mn_help = Menu(menubar, tearoff=0)
        mn_help.add_command(label="Help Index", command=self.mn_help_index)
        mn_help.add_command(label="About…", command=self.mn_help_about)
        menubar.add_cascade(label="Help", menu=mn_help)
        root.config(menu=menubar) # display the menu
        # END MENU

        self.text_area.edit_modified(False)
        self.calselected(None)
        self.text_area.focus()


    def calselected(self, event=None):
        ''' day in calendar was clicked '''
        if self.text_area.edit_modified():
            messagebox.showwarning("Warning!", "Previous changes lost")
            self.text_area.edit_modified(False)
            return
        date_key = self.cal.get_date()
        self.text_area.delete("1.0", END)
        # display text if already in database
        conn = sqlite3.connect('pjourn.db')
        sql = "SELECT entry FROM pj WHERE date_key = '" + date_key + "'"
        cursor = conn.execute(sql)
        txt = cursor.fetchone()

        if txt is not None:
            # load entry into textbox
            self.text_area.insert("1.0", txt[0])
        else:
            # clear textbox
            self.text_area.delete("1.0", END)

        conn.close()
        self.text_area.edit_modified(False)


    def saveoff(self):
        ''' turn off "Saving.." text in Save button '''
        self.btn_save.configure(text="Save")

    def save_entry(self, e=None):
        ''' save entry to database for this date '''
        self.btn_save.configure(text="Saving..")
        date_key = self.cal.get_date()
        entry_text = self.text_area.get("1.0", END)

        conn = sqlite3.connect('pjourn.db')
        sql = "SELECT entry FROM pj WHERE date_key = '" + date_key + "'"
        cursor = conn.execute(sql)
        txt = cursor.fetchone()

        if txt is not None:
            # update entry for this date
            conn.execute("UPDATE pj SET entry=? WHERE date_key=?", \
                        [entry_text, date_key])
        else:
            # insert new entry for this date
            conn.execute("INSERT INTO pj VALUES (?, ?)", \
                         [date_key, entry_text])

        self.text_area.edit_modified(False)
        conn.commit()
        conn.close()
        root.after(1500, self.saveoff)


    def list_all(self):
        ''' Creates a text file for the year, and
        executes your text editor to display text. '''
        date_key = self.cal.get_date()
        year_key = date_key[:4]  # just the year
        conn = sqlite3.connect('pjourn.db')
        sql = f"SELECT date_key, entry FROM pj WHERE date_key LIKE '{year_key}%'"
        print(sql)
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        fh = open("output.txt", 'w')
        for rec in rows:
            txt = ">>> " + rec[0] + "\n"
            txt += rec[1].rstrip() + "\n"
            txt += "....................................................................\n"
            fh.write(txt)
        fh.close()
        conn.close()
        subprocess.Popen([self.tedit, 'output.txt'])

    def insert_time(self, event):
        ''' inserts 12 hour time at cursor '''
        time = strftime("%I:%M %p") + " "
        inx = self.text_area.index(INSERT)
        self.text_area.insert(inx, time)

    def spellcorrect(self, event):
        ''' This spell checker is not great;
        so just display the suggested spelling, but
        do not autocorrect the actual text '''
        if self.text_area.tag_ranges("sel"):
            text = self.text_area.selection_get()
            entry_text = self.spell(text)
            if entry_text != text:
                messagebox.showinfo("Correction?",
                                    "Perhaps you were thinking of:\n" + entry_text)

    def insert_macro(self, event):
        ''' macro text from .py.cfg file
        user pressed Ctrl- 1, 2, or 3 '''
        key = int(event.keysym)
        inx = self.text_area.index(INSERT)
        if key == 1:
            self.text_area.insert(inx, self.mac1)
        elif key == 2:
            self.text_area.insert(inx, self.mac2)
        else:
            self.text_area.insert(inx, self.mac3)


    def exit_program(self, e=None):
        ''' user must save changes before quitting '''
        if self.text_area.edit_modified():
            messagebox.showwarning("Warning!", "Previous changes will be lost")
            return
        save_location()  # closes the application

    # MENU handlers

    def nm_file_save(self):
        ''' menu action '''
        self.save_entry()

    def nm_file_exit(self):
        ''' menu action '''
        self.exit_program()

    def mn_edit_undo(self):
        ''' menu action '''
        self.text_area.edit_undo()

    def mn_edit_redo(self):
        ''' menu action '''
        self.text_area.edit_redo()

    def mn_edit_selall(self, e=None):
        ''' menu action '''
        self.text_area.tag_add(SEL, '1.0', END)
        self.text_area.mark_set(INSERT, '1.0')
        self.text_area.see(INSERT)

    def mn_edit_copy(self):
        ''' menu action '''
        if self.text_area.tag_ranges("sel"):
            text = self.text_area.selection_get()
            root.clipboard_clear()  # clear clipboard contents
            root.clipboard_append(text)  # append new value to clipbaord

    def mn_edit_paste(self):
        ''' menu action '''
        text = root.clipboard_get()
        inx = self.text_area.index(INSERT)
        self.text_area.insert(inx, text)

    def mn_edit_mac1(self):
        ''' menu action '''
        inx = self.text_area.index(INSERT)
        self.text_area.insert(inx, self.mac1)
    def mn_edit_mac2(self):
        ''' menu action '''
        inx = self.text_area.index(INSERT)
        self.text_area.insert(inx, self.mac2)
    def mn_edit_mac3(self):
        ''' menu action '''
        inx = self.text_area.index(INSERT)
        self.text_area.insert(inx, self.mac3)

    def mn_help_index(self):
        ''' menu action '''
        webbrowser.open("https://github.com/MLeidel/personalJournal/blob/main/README.md")

    def mn_help_about(self):
        ''' menu action '''
        messagebox.showinfo("About", "Personal Journal\nBy M D Leidel")

    # END MENU handlers

# END Application Class


def save_location(e=None):
    ''' executes at WM_DELETE_WINDOW event - see below '''
    with open("winfo", "w") as fout:
        fout.write(root.geometry())
    # if config file exists then backup to cloud
    if os.path.exists(".pj_ftp.cfg"):
        myftp_upload(".pj_ftp.cfg")

    root.destroy()


def myftp_upload(confile):
    ''' option for saving database to cloud '''
    config = configparser.RawConfigParser()
    config.read(confile)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(config.get('Main','hostname'),
                username=config.get('Main','hostuser'),
                password=config.get('Main','hostpass'),
                cnopts=cnopts) as sftp:
        with sftp.cd(config.get('Main','hostpath')):
            for n in range(1, config.getint('Main','files') + 1):
                fnum = "f" + str(n)
                print('uploading: ', config.get('Main',fnum))
                sftp.put(config.get('Main',fnum))

def myftp_download(confile):
    ''' option for saving database to cloud '''
    config = configparser.RawConfigParser()
    config.read(confile)
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    spath = config.get('Main','hostpath')
    with pysftp.Connection(config.get('Main','hostname'),
                username=config.get('Main','hostuser'),
                password=config.get('Main','hostpass'),
                cnopts=cnopts) as sftp:
        with sftp.cd(spath):
            for n in range(1, config.getint('Main','files') + 1):
                fnum = "f" + str(n)
                fname = os.path.basename(config.get('Main',fnum))
                print('downloading: ', fname)
                sftp.get(fname, config.get('Main',fnum))


root = ThemedTk(theme="radiance")
## NOTE: ScrolledText does NOT follow ThemedTK !

# change working directory to path for this file
p = os.path.realpath(__file__)
os.chdir(os.path.dirname(p))

# SAVE GEOMETRY INFO
if os.path.isfile("winfo"):
    with open("winfo") as f:
        lcoor = f.read()
    root.geometry(lcoor.strip())
else:
    root.geometry("520x430") # WxH+left+top


root.title("Personal Journal")
root.protocol("WM_DELETE_WINDOW", save_location)  # SAVE GEOMETRY INFO
Sizegrip(root).place(rely=1.0, relx=1.0, x=0, y=0, anchor=SE)
app = Application(root)
app.mainloop()
