# lunlumo.py splits files into QR code loops for file transfer
# Copyright (C) 2017-2018  u/NASA_Welder
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import print_function

import sys
if sys.version_info < (3,):
    import Tkinter as tk
    def b(x):
        return x
else:
    import tkinter as tk
    import tkinter
    import tkinter.ttk as ttk
    import tkinter.ttk
    import tkinter.filedialog as FileDialog
    import tkinter.messagebox as MessageBox
    #import codecs
    def b(x):
        #return codecs.latin_1_encode(x)[0]
        return x.decode("utf-8")

## lunlumo libraries
import wallet_expect as wex

## external libraries
import pyqrcode
import zlib
from PIL import Image, ImageTk
##

## python stdlib
from math import ceil
import base64
import argparse
import hashlib
import math
import os
import os.path
#import Tkinter as tk
from glob import glob

import webbrowser as web
##

# Monero donations to nasaWelder (babysitting money, so I can code!)
# 48Zuamrb7P5NiBHrSN4ua3JXRZyPt6XTzWLawzK9QKjTVfsc2bUr1UmYJ44sisanuCJzjBAccozckVuTLnHG24ce42Qyak6

class Lunlumo(ttk.Frame):
    def __init__(self,app, parent,walletFile = None, password = '',daemonAddress = None, daemonHost = None,testnet = False,cold = True, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.wallet = wex.Wallet(walletFile, password,daemonAddress, daemonHost,testnet,cold,gui=True)
        self.sidebar = Sidebar(app,self)
        self.statusbar = Statusbar(app,self)

        self.sidebar.grid(row=0,column = 0)
        self.statusbar.grid(row=2,column = 0, columnspan =3)

class Sidebar(ttk.Frame):
    def __init__(self,app, parent, delay = 21000, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.delay = delay
        self.logo = tk.PhotoImage(file = "misc/lunlumo8bitsmall.gif")
        self.showLogo = ttk.Label(self,image= self.logo)
        self.balFrame =  tk.Frame(self,highlightcolor = "white",highlightbackground = "white",highlightthickness=3,background ="#4C4C4C")
        self.balance = ttk.Label(self.balFrame,text = "Balance:   X.XXXXXXXXXXXX",style = "app.TLabel",)
        self.unlocked = ttk.Label(self.balFrame,text ="Unlocked: X.XXXXXXXXXXXX",style = "app.TLabel",)
        self.balance.grid(row=0,column=0,sticky=tk.W,padx =(5,0),pady=(5,1))
        self.unlocked.grid(row=1,column=0,sticky=tk.W,padx =(5,0),pady=(0,5))

        self.showLogo.grid(row=0,column=0,sticky=tk.W)
        self.balFrame.grid(row=1,column=0,sticky=tk.W+tk.E)
        self._root().after(4000,self.refresh)
    def refresh(self):
        if self.parent.wallet.ready:
            now = self.parent.wallet.balance() #.replace(", unlocked balance","unlocked balance")
            bal = now.split(",")[0].replace("Balance:","Balance:  ")
            unlockedbal = now.split(",")[1].replace(" unlocked balance:","Unlocked:")
            self.balance.configure(text = bal)
            self.unlocked.configure(text = unlockedbal)
            self._root().after(self.delay,self.refresh)
        else:
            self._root().after(5000,self.refresh)
class Statusbar(ttk.Frame):
    def __init__(self,app, parent,delay = 55000, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.delay = delay
        self.status = ttk.Label(self,text = "Checking Status...",style = "app.TLabel")
        self.status.grid(row = 0, column =0)
        self._root().after(2000,self.refresh,False)
    def refresh(self,subRefresh = True):
        if self.parent.wallet.ready:
            now = self.parent.wallet.status(refresh=subRefresh)
            self.status.configure(text = now)
            self._root().after(self.delay,self.refresh)
        else:
            self._root().after(5000,self.refresh)


class PaneSelect(ttk.Frame):
    def __init__(self,app, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent

class Pane(ttk.Frame):
    def __init__(self,app, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent

class FilePicker(ttk.Frame):
    def __init__(self,app, parent,handle,start = None,buttonName = "Select",askPass = False,ftypes = [("all","*")],idir="./", *args, **kwargs):
        tk.Frame.__init__(self, parent,highlightcolor = "white",highlightbackground = "white",highlightthickness=3,background ="#4C4C4C" , *args, **kwargs)
        self.app = app
        self.parent = parent
        self.handle = handle
        self.ftypes = ftypes
        self.idir = idir
        self.askPass = askPass
        self.title = ttk.Label(self,text = self.handle,style = "app.TLabel")
        self.displayVar = tk.StringVar()
        self.displayVar.set("*")
        self.selectVar = tk.StringVar()
        self.selectVar.set("")
        self.passlbl = ttk.Label(self,text = "password:",style = "app.TLabel")
        self.password = tk.Entry(self,text = self.handle,insertofftime=5000,show = "*",width = 13,foreground = "white")
        if start:
            self.selectVar.set(start)
            self.displayVar.set(os.path.basename(choice))
        self.select = ttk.Label(self,textvariable = self.displayVar,wraplength=210,style = "app.TLabel")
        self.button = ttk.Button(self,text = buttonName,style = "app.TButton",command =self.dialog )

        self.title.grid(row = 0,column = 0,padx=(5,0))
        self.button.grid(row = 0,column = 1,padx=6,pady = 6)
        self.select.grid(row = 1,column = 0,sticky = tk.W,columnspan = 3,padx=(5,0),pady=(0,3))
        if self.askPass:
            self.passlbl.grid(row = 2,column = 0,sticky = tk.W,padx=(5,5))
            self.password.grid(row = 2,column = 1,sticky = tk.W,padx=(0,0),pady = (0,8))

    def dialog(self):
        choice = FileDialog.askopenfilename(filetypes=self.ftypes,initialdir = self.idir,title = self.handle)
        self.password.delete(0,tk.END)
        if choice:
            self.displayVar.set(os.path.basename(choice))
            self.selectVar.set(choice)
        else:
            self.displayVar.set("*")
            self.selectVar.set("")
    def get(self):
        if not self.askPass:
            if self.selectVar.get() == "":
                return None
            return self.selectVar.get()
        else:
            if self.selectVar.get() == "":
                return None,None
            return self.selectVar.get(),self.password.get()

class Login(ttk.Frame):
    def __init__(self,app, parent,*args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.final = None

        self.logo = tk.PhotoImage(file = "misc/legitmoonsmaller.gif")
        self.showLogo = ttk.Label(self,image= self.logo,style = "app.TLabel",cursor = "shuttle")
        #heading = ttk.Label(first,text= "Wallet Options",style = "app.TLabel")
        self.walletFile = FilePicker(self.app,self,"Wallet File",askPass = True,start = None,ftypes = [("full","*.keys"),("watchonly","*.keys-watchonly")],idir="./")
        self.testnet = MyWidget(self.app,self,handle = "testnet",optional = 1,)
        self.launch = ttk.Button(self,text = "Launch!",style = "app.TButton",command =self.launch,cursor = "shuttle" )
        #MyWidget(app, parent,handle,choices=None,subs = {},allowEntry = False,optional = False,activeStart=1,ewidth = 8,cwidth = None, cmd = None)
        self.daemon = MyWidget(self.app,self,handle = "daemon",startVal = "None (cold wallet)",allowEntry = False,cwidth = 18,cipadx = 1,
                                choices = ["None (cold wallet)","default, already running","daemonHost","daemonAddress"],
                               subs={"daemonHost":{"handle":"host","choices":"entry","ewidth":20,"allowEntry":False},  # allowEntry is for comboboxes when choices is a list
                                     "daemonAddress":{"handle":"host","choices":"entry","ewidth":20,"allowEntry":False,
                                                       "subs":{"entry":{"handle":"port","choices":"entry","ewidth":20,"allowEntry":False}},
                                                      },
                                     })

        self.showLogo.grid(row=0,column=0,rowspan=1,sticky=tk.NW,columnspan=2)
        #self.heading.grid(row=0,column=1,sticky=tk.W)
        self.walletFile.grid(row=1,column=0,sticky=tk.NW,padx=5,pady=(5,0),columnspan=2)
        self.testnet.grid(row=3,column=0,sticky=tk.NW,padx=(5,0),pady=10)
        self.launch.grid(row=3,column=1,sticky=tk.NW,padx=(5,0),pady= 5)
        self.daemon.grid(row=2,column=0,pady=(10,15),rowspan=1,columnspan=2)
    def launch(self):
        wallet = self.walletFile.get()
        vals = {"walletFile": wallet[0],"password": wallet[1],"testnet":bool(self.testnet.get()),}
        daemon = self.daemon.get()
        if daemon[0] == "None (cold wallet)":
            vals.update({"cold":True})
        elif  daemon[0] == "default, already running":
            vals.update({"cold":False})
        elif daemon[0] == "daemonHost":
            vals.update({"daemonHost":daemon[1]})
            vals.update({"cold":False})
        elif daemon[0] == "daemonAddress":
            vals.update({"daemonAddress":daemon[1]+ ":" + daemon[2] })
            vals.update({"cold":False})

        self.final = vals
        self.app.destroy()


class MyWidget(ttk.Frame):
    def __init__(self,app, parent,handle,choices=None,subs = {},startVal = None,allowEntry = False,
                 cipadx = 0,optional = False,activeStart=1,ewidth = 8,cwidth = None, cmd = None, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.handle = handle
        self.choices = choices
        self.optional = optional
        self.allowEntry = allowEntry
        self.startVal = startVal
        self.cmd = cmd
        self.subs = subs
        self.sub = None
        if self.optional:
            self.optState = tk.IntVar()
            self.optBut = ttk.Checkbutton(self,variable = self.optState,onvalue = 1,offvalue=0,command = self._grey,style = "app.TCheckbutton")
            self.optBut.pack(side="left")
        if isinstance(self.choices,__builtins__.list):
            if not allowEntry:
                state = "readonly"
            else:
                state = "enabled"
            if not cwidth: cwidth = len(max(self.choices,key=len))
            self.value = ttk.Combobox(self,values = self.choices,state = state,width=cwidth,style = "app.TCombobox")
            self.value.bind('<<ComboboxSelected>>',self.findSubs)
        if self.choices == "entry":
            self.value = ttk.Entry(self,width=ewidth,style = "app.TEntry")
            self._root().after(0,self.findSubs)

        self.title = ttk.Label(self, text = self.handle,style = "app.TLabel")
        self.title.pack(anchor = tk.E)
        if self.choices:
            self.value.pack(anchor = tk.E,ipadx = cipadx)
            if self.startVal:
                self.value.set(self.startVal)
                self._root().after(0,self.findSubs)
        if self.optional:
            if activeStart:
                self.optState.set(1)

    def get(self):
        #print(self.handle,self.sub,bool(self.sub))
        if self.choices:
            if self.sub:
                val = [self.value.get()]
                try:
                    val.extend(self.sub.get())
                except TypeError:
                    print(self.handle,self.sub,bool(self.sub))
                return val
            return [self.value.get()]
        elif self.optional:
            if self.optState.get():
                if self.sub:
                    val = [self.value.get()]
                    try:
                        val.extend(self.sub.get())
                    except TypeError:
                        print(self.handle,self.sub,bool(self.sub))
                    return val
                return [self.handle]
            else:
                return None
        #else:
          #  raise Exception("Widget Error: Unknown value for %s" % self.handle)
    def findSubs(self,event = None):
        if self.sub:
            self.sub.destroy()
            self.sub = None
        if self.subs:
            if self.value.get() in self.subs and not self.choices == "entry":
                self.sub = MyWidget(self.app,self,**self.subs[self.value.get()])
                self.sub.pack(anchor = tk.E,pady=3)
            elif self.choices == "entry":
                self.sub = MyWidget(self.app,self,**self.subs["entry"])
                self.sub.pack(anchor = tk.E,pady=3)
            else:
                pass
        if self.cmd:
            self.cmd()

    def _grey(self,override = False):
        if self.optional and self.choices:
            if not self.optState.get():
                self.value.config(state="disabled")
            else:
                if isinstance(self.value,tkinter.ttk.Combobox):
                    if self.allowEntry:
                        self.value.config(state="enabled")
                    else:
                        self.value.config(state="readonly")
                else:
                    self.value.config(state="enabled")
        if self.sub:
            self.sub._grey()




class SendFrame(ttk.Frame):
    def __init__(self,app,parent,payloadType,payloadPath,PAGE_SIZE = 1000,delay = 1100,width = 350, height = 400,*args,**kargs):
        ttk.Frame.__init__(self,parent,height = height, width = width,style = "app.TFrame", *args,**kargs)
        #global slides
        self.app = app
        self.checksum = crc(payloadPath)
        self.skip = []
        self.delay = delay
        self.PAGE_SIZE = PAGE_SIZE
        self.payloadType = payloadType
        ##################################
        # Create QR images
        self.slides = []
        self.codes = []
        with open(payloadPath, "rb") as source:
            self.payload = base64.b64encode(source.read())

        self.numQR = ceil(len(self.payload)/self.PAGE_SIZE)
        if self.numQR >= 1000:
            raise Exception("%s QRs!! file really got out of hand, exiting"% self.numQR)

        """
        j = 1
        x = 0
        while True:
            chunk = self.payload[x: x+self.PAGE_SIZE]
            if not chunk:
              self.numQR = j-1
              #print("\tQR codes:\t\t%s"%numQR)
              break
            if j>=1000:
                raise Exception("file really got out of hand, exiting")
            j+=1
            x += self.PAGE_SIZE
        """
        self.i = 1
        self.x = 0
        self.make_slides()

        #################################

        self.title = ttk.Label(self,text = "Point Camera Here to Recieve: %s %s" % (payloadType,os.path.basename(payloadPath)),style = "app.TLabel")
        self.crclbl = ttk.Label(self,text = "crc32: %s" % self.checksum,style = "app.TLabel")
        self.ticker = ttk.Label(self,text = "X / X",style = "app.TLabel")
        self.current = ttk.Label(self,style = "app.TLabel")

        self.title.grid(row=0,column = 0,columnspan=3,sticky=tk.W)
        self.crclbl.grid(row=1,column = 0,sticky=tk.W,)
        self.ticker.grid(row=1,column = 1,sticky=tk.W,)
        self.current.grid(row=2,column = 0,columnspan=5,sticky=tk.W)
    def make_slides(self):
        chunk = self.payload[self.x: self.x+self.PAGE_SIZE]
        if chunk:
            heading = self.payloadType + "," + self.checksum + "," + str(self.i) + "/" + str(int(self.numQR)) + ":"
            page = heading + b(chunk)
            qrPage = pyqrcode.create(page,error="L")
            #saved = qrPage.svg(heading.replace(",","_").replace(":","_").replace("/","_") + ".svg")
            code = tk.BitmapImage(data=qrPage.xbm(scale=3))
            code.config(background="white")
            #exec("self.i%s = code"% self.i)
            self.slides.append(code)
            self.i+=1
            self.x += self.PAGE_SIZE
            root.after(100, self.make_slides)

    def refresh(self,ind):
        while ind in self.skip:
            ind += 1
        try:
            slide = self.slides[ind]
            self.ticker.configure(text = "%s / %s" % (ind+1,self.numQR))
            self.current.configure(image=slide)
        except IndexError:
            ind = 0
        else:
            ind += 1
        if ind >= self.numQR: ind =0
        root.after(self.delay, self.refresh, ind)










################################
################################
### Legacy Functions
def crc(fileName):
    prev = 0
    for eachLine in open(fileName,"rb"):
        prev = zlib.crc32(eachLine, prev)
    return "%x"%(prev & 0xFFFFFFFF)

def restricted_delay(x):
    x = float(x)
    if x <= 0.1 or x > 100.0:
        raise argparse.ArgumentTypeError("%r not in range (0.1, 100.0]"%(x,))
    return x

def send(args):
    global frames
    PAGE_SIZE = int(args["bytes"])

    actualOutDir =  os.path.realpath(os.path.join(args["outDir"],os.path.basename(args["infile"]) + ".QRbatch"))
    os.makedirs(actualOutDir)

    bitPath = os.path.join(actualOutDir,'bits')  # TODO get rid of a physical file for bits, just need the string

    with open(args["infile"], "rb") as source:
        with open(bitPath, 'wb') as dest:
            dest.write(base64.b64encode(source.read()))

    checksum = crc(args["infile"])
    print("\n\t%s crc32:\t%s" %(args["infile"],checksum))
    print("\n\t%s crc32:\t%s" %(bitPath,crc(bitPath)))
    fsize = os.path.getsize(args["infile"])
    print("\tfile size:\t\t%s bytes" % fsize)
    pages = math.ceil(float(fsize) / float(PAGE_SIZE))



    #with open(args["infile"],"rb") as f:
    with open(bitPath, 'rb') as f:
      k = 1
      while True:
        chunk = f.read(PAGE_SIZE)
        if not chunk:
          numQR = k-1
          print("\tQR codes:\t\t%s"%numQR)
          break
        if k>=200:
            print("file really got out of hand, exiting")
            break
        k+=1
    with open(bitPath, 'rb') as f:
      i = 1
      frames = []
      while True:
        heading = args["msgType"] + "," + str(checksum) + "," + str(i) + "/" + str(int(numQR)) + ":"
        chunk = f.read(PAGE_SIZE)


        if not chunk:
          numQR = i-1
          print("\n\tEnd of file reached, %s QR codes"%numQR)
          print("\tOutput dir:\t\t%s"%actualOutDir)
          break
        if i>=200:
            print("file really got out of hand, exiting")
            break

        page = heading + b(chunk)
        pageName = os.path.basename(args["infile"]) + "_" + str(checksum) + "_" + str(i) + "of" + str(int(numQR))
        qrPage = pyqrcode.create(page,error="L")
        #print(qrPage.text())
        pagePath = os.path.join(actualOutDir,pageName)
        if "htmlOutput" in args and args["htmlOutput"]:
            saved = qrPage.svg(pagePath + ".svg")
            saved2 = qrPage.eps(pagePath+".eps",scale=3.5,)
        #frames.append( ImageTk.PhotoImage( Image.open( pagePath+".eps" ) ) )
        code = tk.BitmapImage(data=qrPage.xbm(scale=4))
        code.config(background="white")
        frames.append(code)
        i+=1

    if "htmlOutput" in args and args["htmlOutput"]:
        args=dict(args)
        args.update({"actualOutDir":actualOutDir,"numQR":numQR,"checksum":checksum})
        htmlOutput(args)

    return frames,actualOutDir

def htmlOutput(args):
    htmlfile = open(os.path.join(args["actualOutDir"],"all.html"), "w")
    htmlfile.write("<!DOCTYPE html>\n<html>\n<body>\n")
    htmlfile.write('<table cellpadding="35">\n<tr><th>qrcode</th><th>file</th></tr>\n')
    for filename in sorted(os.listdir(args["actualOutDir"])):
        #print("filename: ", filename)
        if filename.endswith(".svg"):
            htmlfile.write('<tr>\n')
            htmlfile.write('<td><img src = "' + os.path.join(args["actualOutDir"],filename) + '" alt ="cfg" align = "left" height="500" width="500"></td><td>%s</td>\n' % os.path.join(args["actualOutDir"],filename))
            htmlfile.write('</tr>\n')


    htmlfile.write('</table>\n')
    htmlfile.write("</body>\n</html>\n")
    htmlfile.close()

    loopfile = open(os.path.join(args["actualOutDir"],"loop.html"), "w")
    base = os.path.basename(args["infile"]) + "_" + str(args["checksum"]) + "_"
    last = "of" + str(args["numQR"]) + ".svg"
    firstImg = base + str(1) + last
    loopfile.write("""
<html>
<head>
</head>

<body>
<div> Directory: %(outDir)s <div>
<div> src name: %(src)s <div>
<div> src crc32: %(check)s <div>

<table cellpadding="5">\n<tr><th></th><th></th><th></th></tr>
<td><img src="%(outDir)s/%(firstImg)s" alt="ERROR in QR code processing" width="500" height="500" id="rotator"></td><td><div id="theName">X of X</div></td><td width= "600px"><div><iframe width= "600px" height="500px" src="../html/recvStatus.htm" name="recvStatusName" id="recvStatus"></iframe></div></td></table>
<p>Monero donations to nasaWelder (babysitting money, so I can code!)</p>
<p>48Zuamrb7P5NiBHrSN4ua3JXRZyPt6XTzWLawzK9QKjTVfsc2bUr1UmYJ44sisanuCJzjBAccozckVuTLnHG24ce42Qyak6</p>

<script type="text/javascript">
(

function() {

    var rotator = document.getElementById('rotator'), //get the element
        dir = '%(outDir)s',                              //images folder
        base = '%(base)s',
        last = '%(last)s',
        delayInSeconds = %(delay)s,                           //delay in seconds
        num = 1,                                      //start number
        len = %(N)s;                                      //limit

    //var rfile = './recvStatus.txt';

    setInterval(function(){                           //interval changer
        rotator.src = dir + base + num+ last + '.svg';               //change picture
        rotator.alt = base + num+ last + '.svg';
        document.getElementById('theName').innerHTML = '                 ' +num + ' of ' + len + '               ' ;

        document.getElementById('recvStatus').src = document.getElementById('recvStatus').src;    // idk how to display text from file...
        num = (num === len) ? 1 : ++num;              //reset if last image reached
    }, delayInSeconds * 1000);
}());
</script>
</body>
</html>
""" % {"outDir" : args["actualOutDir"] + "/" ,"firstImg": firstImg,"N" : args["numQR"],"base" :base,"last":last.replace(".svg",""),"src": os.path.basename(args["infile"]),"check":args["checksum"], "delay": args["delay"]})
    loopfile.close()
    displayLoop(sendDir=args["actualOutDir"])

def stitch(args):
    actualOutDir =  os.path.realpath(os.path.join(args["outDir"],os.path.basename(args["infile"]) + ".QRstitched"))
    os.makedirs(actualOutDir)
    stitchPath = os.path.join(actualOutDir,os.path.basename(args["infile"]) +".stitched")
    with open(args["infile"], "rb") as source:
        with open(stitchPath, 'wb') as dest:
            data = source.read().strip()
            print(len(data)%4)
            missing_padding = len(data) % 4
            if missing_padding != 0:
                data += b'='* (4 - missing_padding)
                print(len(data)%4)
            dest.write(base64.b64decode(data))

    print("\n\t%s crc32:\t%s" %(args["infile"],crc(args["infile"])))
    print("\n\t%s crc32:\t%s" %(stitchPath,crc(stitchPath)))



def displayLoop(sendDir):
    web.open_new(os.path.realpath(sendDir) + "/loop.html")
    imageNames = glob(os.path.realpath(sendDir) + "/*.svg")
    #print(imageNames)
    i = 0
    #sendImages = [tk.PhotoImage(file=sendDir + img) for img in imageNames]


def updateStatus(info):
    # list of lines for status iframe
    with open("./html/recvStatus.htm","w") as status:
        status.write('''<html>
<head>
</head>

<body>
        ''')
        for i in info:
            status.write("<div>%s</div>"% i)
        status.write('''</body>
</html>''')

def update(ind):
    global frames
    frame = frames[ind]
    ind += 1
    label.configure(image=frame)
    if ind ==len(frames): ind =0
    root.after(1100, update, ind)



parser = argparse.ArgumentParser(description='Generate bulk qr code')
subparsers = parser.add_subparsers()
sendParser = subparsers.add_parser('send')
sendParser.add_argument('msgType', choices = ["signed_tx","unsigned_tx","watch-only","public_address","raw"],
                    help='heading for qrcodes')
sendParser.add_argument('infile',
                    help='file to be converted to QR code batch')
sendParser.add_argument('--delay', default="1.1", type=restricted_delay,
                    help='delay in seconds after which QR code will transition to next QR code.')
sendParser.add_argument('--bytes', default=1000, choices=range(50, 2500), type=int,
                    help='how many bytes to stuff in QR code.')
sendParser.add_argument('--outDir', default="./",
                    help='dir to place QR code batch')
sendParser.add_argument('--htmlOutput', action='store_true',
                    help='old way: pop out a browser tab showing loop')
sendParser.set_defaults(func=send)

stitchParser = subparsers.add_parser("stitch")
stitchParser.add_argument('infile',
                    help='file to be converted to monero format')
stitchParser.add_argument('--outDir', default="./",
                    help='dir to place stitched together file')
stitchParser.set_defaults(func=stitch)



if __name__ == "__main__":
    first = tk.Tk()
    first.configure(bg="#F2681C")
    first.title("Wallet Options")
    style = ttk.Style()
    style.theme_use('clam') #('clam', 'alt', 'default', 'classic')
    style.configure("app.TLabel", foreground="white", background="#4C4C4C")
    style.configure("app.TFrame", foreground="white", background="#4C4C4C",)
    style.configure("app.TButton", foreground="white", background="#F2681C",activeforeground ="#F2681C" )
    style.configure("app.TCheckbutton", foreground="white", background="#4C4C4C")
    style.configure("app.TCombobox", background="#F2681C")
    style.configure("app.TEntry", foreground="black", background="white")
    style.configure("pass.TEntry", foreground="white", background="white",insertofftime=5000)

    login = Login(first,first)
    login.pack()
    first.mainloop()

    #################################
    if login.final:
        root = tk.Tk()
        style = ttk.Style()
        style.theme_use('clam') #('clam', 'alt', 'default', 'classic')
        style.configure("app.TLabel", foreground="white", background="#4C4C4C")
        style.configure("app.TFrame", foreground="white", background="#4C4C4C",)
        style.configure("app.TButton", foreground="white", background="#F2681C",activeforeground ="#F2681C" )
        style.configure("app.TCheckbutton", foreground="white", background="#4C4C4C")
        style.configure("app.TCombobox", background="#F2681C")
        style.configure("app.TEntry", foreground="black", background="white")
        style.configure("pass.TEntry", foreground="white", background="white",insertofftime=5000)

        try:
            App = Lunlumo(root,root,**login.final)
        except Exception as e:
            MessageBox.showerror("Wallet Error",str(e))
        else:
            App.grid(row=0,column=0)
        root.mainloop()

        App.wallet.stopWallet()
        sys.exit(0)
    """
    root = tk.Tk()

    sendme = SendFrame(root,root,"raw","signed_monero_tx",)
    sendme.skip = [1,2,3,4,7,8,9,13,14,15,16,17,18,19]

    sendme.grid(row=0,column=0,)
    sendme.grid_propagate(False)
    root.after(0,sendme.refresh,0)
    root.mainloop()
    """
    ########################################################
    sys.exit(0)
    args = parser.parse_args()
    for arg in vars(args):
        print("\t%s\t\t%s"% (arg, getattr(args, arg)))
    try:
        root = tk.Tk()

        frames,out = args.func(args.__dict__)

        label = tk.Label(root)
        button = tk.Button(root,text="allo!")
        label.grid(row = 0,column=0)
        button.grid(row = 1,column = 0)
        root.after(0, update, 0)
        root.mainloop()
    except:
        raise

