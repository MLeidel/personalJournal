'''
code file: pj.py
Personal Journal
'''
from tkinter import *
from tkinter.ttk import *  # defaults all widgets as ttk
from tkcalendar import *
from tkinter import scrolledtext
import sqlite3
import pysftp
import configparser
import os
import subprocess
from time import gmtime, strftime
from tkinter.font import Font
from tkinter import messagebox
from autocorrect import Speller
from ttkthemes import ThemedTk  # ttkthemes is applied to all widgets

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

        self.create_widgets()
        self.spell = Speller(lang='en')


    def create_widgets(self):
        ''' creates GUI for app '''

        myfont = Font(family='Lucida Console', weight='normal', size=11)
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

        btn_save = Button(frm, text="Save", command=self.save_entry)
        btn_save.grid(row=1, column=1, pady=5, padx=10)
        btn_print = Button(frm, text="List", command=self.list_all)
        btn_print.grid(row=1, column=2, pady=5, padx=10)
        btn_close = Button(frm, text="Close", command=save_location)
        btn_close.grid(row=1, column=3, pady=5, padx=10)

        root.bind("<<CalendarSelected>>", self.calselected)
        root.bind('<Control-s>', self.save_entry)
        root.bind('<Control-q>', save_location)
        root.bind('<Escape>', exit)
        self.text_area.bind('<Control-t>', self.insert_time)


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


    def save_entry(self):
        ''' save entry to database for this date '''
        date_key = self.cal.get_date()
        etext = self.text_area.get("1.0", END)

        # run through spell checker
        #   and update Text widget
        entry_text = self.spell(etext)
        self.text_area.delete("1.0", END)
        self.text_area.insert("1.0", entry_text)

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

    def list_all(self):
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
        subprocess.Popen(['gedit', 'output.txt'])

    def insert_time(self, event):
        time = strftime("%I:%M %p") + " "
        inx = self.text_area.index(INSERT)
        self.text_area.insert(inx, time)  # paste into


# END Application Class

# UNCOMMENT THE FOLLOWING TO SAVE GEOMETRY INFO
def save_location(e=None):
    ''' executes at WM_DELETE_WINDOW event - see below '''
    # ans = messagebox.askokcancel("Data Saved", "Ok to exit?")
    # if ans is not True:
    #     return
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
