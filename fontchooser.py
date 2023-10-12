from tkinter import *
from tkinter import font
from configparser import ConfigParser

class Application(Frame):
    ''' main class docstring '''
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.pack(fill=BOTH, expand=True, padx=4, pady=4)

        config.read(".pj.cfg")
        ftsz = config['Main']['fontsize']
        ftfm = config['Main']['fontname']

        #persistent font reference
        self.textfont = font.Font(family=ftfm, size=ftsz)
        
        #something to type in ~ uses the persistent font reference
        tx = Text(self, font=self.textfont)
        tx.grid(row=0, column=0, sticky='nswe')
        tx.delete(1.0,END)
        tx.insert(END, "Hello There\n12345\n@ # $ % & * (hello)")
        
        #make the textfield fill all available space
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        #font chooser
        self.fc = Listbox(self)
        self.fc.grid(row=0, column=1, sticky='nswe')

        #insert all the fonts
        for f in font.families():
            self.fc.insert('end', f)

        btn_close = Button(self, text='Save & Close', command=self.saveClose)
        btn_close.grid(row=1, column=0, sticky='ew')

        self.fontsize = Entry(self, width=4)
        self.fontsize.grid(row=1, column=1)
        self.fontsize.delete(0,END)
        self.fontsize.insert(0,'14')
        self.fc.bind('<ButtonRelease-1>', self.getfont )
        
        #scrollbar ~ you can actually just use the mousewheel to scroll
        vsb = Scrollbar(self)
        vsb.grid(row=0, column=2, sticky='ns')
        #connect the scrollbar and font chooser
        self.fc.configure(yscrollcommand=vsb.set)
        vsb.configure(command=self.fc.yview)


    def getfont(self, e=None):
        fontfam = self.fc.get(self.fc.curselection())
        fontsize = self.fontsize.get()
        self.textfont.config(family=fontfam)
        self.textfont.config(size=fontsize)
        config['Main']['fontname'] = fontfam
        config['Main']['fontsize'] = fontsize

    def saveClose(self):
        with open(".pj.cfg", 'w') as configfile:
            config.write(configfile)
        root.destroy()

config = ConfigParser()
root = Tk()
root.title('PJ Font Chooser')
root.geometry(f'400x400')
app = Application(root)
app.mainloop()
