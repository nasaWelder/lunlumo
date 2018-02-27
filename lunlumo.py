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
    import tkinter.simpledialog as SimpleDialog
    #import codecs
    def b(x):
        #return codeqcs.latin_1_encode(x)[0]
        return x.decode("utf-8")

## lunlumo libraries
import wallet_expect as wex
from scanner import Payload

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
import re
#import Tkinter as tk
from glob import glob

import webbrowser as web
##

# Monero donations to nasaWelder (babysitting money, so I can code!)
# 48Zuamrb7P5NiBHrSN4ua3JXRZyPt6XTzWLawzK9QKjTVfsc2bUr1UmYJ44sisanuCJzjBAccozckVuTLnHG24ce42Qyak6

class Lunlumo(ttk.Frame):
    def __init__(self,app, parent,walletFile = None, password = '',background ="misc/genericspace2.gif",daemonAddress = None, daemonHost = None,testnet = False,cold = True,cmd = "./monero-wallet-cli",camera_choice = None,light = False, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.busy = False
        self.cancel = False
        self.cold = cold
        self.light = light
        self.background = background
        if "monero-wallet-cli" in os.path.basename(cmd):
            self.coin = "monero"
        elif "aeon-wallet-cli" in os.path.basename(cmd):
            self.coin = "aeon"
        else:
            raise Exception("Unknown coin %s" % os.path.basename(cmd))

        self.wallet = wex.Wallet(walletFile, password,daemonAddress, daemonHost,testnet,self.cold,gui=self,postHydra = True,debug = 33,cmd = cmd,coin = self.coin)

        if camera_choice == "webcam (v4l)":
            from scanner import Scanner_pygame
            self.scanner = Scanner_pygame(app = self)
        elif camera_choice == "raspi cam":
            from scanner import Scanner_picamera
            self.scanner = Scanner_picamera(app = self)
        else:
            self.scanner = None
        self.preview = None


        self.initAddress = re.findall(self.wallet.patterns["address"],self.wallet.boot)[0]
        self.address_book_menu = None
        self.subaddress_book_menu = None
        self.account_menu = ["0 %s Primary account (loading tag)" % self.initAddress[:6]]
        self.primary_account = self.account_menu[0]
        self.earliestBalance = 1000
        if True: #self.light:   #light mode solved by removing imagesfrom backgrounds...
            self.full_start()
        else:
            self.coldsignpage = Coldsign(self,self)
            self.coldsignpage.grid(row=0,column = 1 ,sticky=tk.NW+tk.SE,padx=(20,20),pady=(20,20))

    def full_start(self):
        self.bg = tk.PhotoImage(file = "misc/genericspace2.gif")
        self.bg1 = tk.PhotoImage(file = "misc/genericspace.gif")
        self.bg3 = tk.PhotoImage(file = "misc/genericspace3.gif")
        self.bgv = tk.PhotoImage(file = "misc/genericspacev.gif")

        if self.background and not self.light:

            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)
        try:
            self.sidebar = Sidebar(self,self)
            self.statusbar = Statusbar(self,self)
            self.receivepage = Receive(self,self,background = self.background )
            self.donatepage = Donate(self,self)
            if not self.cold:
                self.sendpage = SendPane(self,self,background = self.background )
                self.sendpage.grid(row=0,column = 1 ,sticky=tk.NW+tk.SE,padx=(20,20),pady=(20,20))
            else:
                self.coldsignpage = Coldsign(self,self)
                self.coldsignpage.grid(row=0,column = 1 ,sticky=tk.NW+tk.SE,padx=(20,20),pady=(20,20))
            self.sidebar.grid(row=0,column = 0,sticky=tk.NW)
            self.statusbar.grid(row=2,column = 0, columnspan =3,sticky=tk.W+tk.E)
            self.receivepage.grid(row=0,column = 1 ,sticky=tk.NW+tk.E,padx=(20,20),pady=(20,20))
            self.donatepage.grid(row=0,column = 1 ,sticky=tk.NW+tk.E,padx=(20,20),pady=(20,20))

            #self._root().after(100,self.receivepage.grid_propagate,False)

        except Exception as e:
            self.wallet.stopWallet()
            MessageBox.showerror("Startup Error",str(e))
            raise


        self._root().after(3000,self.receivepage.idle_refresh)
        self._root().after(4000,self.statusbar.idle_refresh,False)

        if not self.cold:
            self._root().after(2500,self.sidebar.refresh_account,True,None)
            self._root().after(25000,self.sendpage.idle_refresh)
        else:

            self._root().after(2500,self.sidebar.refresh_account)
        #self._root().after(10000,self.preview_request)


    def confirm(self,msg):
        return MessageBox.askokcancel("Please Confirm!",msg)
    def wallet_alarm(self,err):
        MessageBox.showerror("Wallet Error",err)
        self.cancel = True
        self.preview_cancel()
    def showinfo(self,msg):
        MessageBox.showinfo("fyi", msg)

    def showerror(self,title,err):
        MessageBox.showerror(title,err)

    def preview_request(self):
        if not self.scanner is None:
            if not self.preview:
                self.preview = Preview(self,self)
                self.scanner.add_child(self.preview)
        else:
            self.showerror("Camera Missing","Unable to display feed, as camera not initialized. This should should have been prevented by upstream logic.")

    def preview_cancel(self):
        if self.preview:
            self.scanner.children.remove(self.preview)
            self.preview.close()
            self.preview = None


    def monitor_incoming(self,payload,when_finished,*args,**kwargs):
        if not payload.got_all():
            self._root().after(self.scanner.delay_ms,self.monitor_incoming,payload,when_finished,*args,**kwargs)
        else:
            self.scanner.children.remove(payload)
            self._root().after(50,when_finished,payload,*args,**kwargs)

    def payload_started(self):
        try:
            self.sender.destroy()
        except Exception as e:
            print(str(e))
        self.sender = None

class Sidebar(ttk.Frame):
    def __init__(self,app, parent, delay = 40000,background = "misc/genericspace3.gif", *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.delay = delay
        self.bg3 = tk.PhotoImage(file = "misc/genericspace3.gif")
        self.bg1 = tk.PhotoImage(file = "misc/genericspace.gif")
        self.bg2 = tk.PhotoImage(file = "misc/genericspace2.gif")
        self.bgv = tk.PhotoImage(file = "misc/genericspacev.gif")
        if background and not self.app.light:

            self.bglabel = tk.Label(self, image=self.bg3)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)
        self.logo = tk.PhotoImage(file = "misc/reddit_user_philkode_made_this.gif")
        self.showLogo = ttk.Label(self,image= self.logo)
        self.balFrame =  tk.Frame(self,highlightcolor = "white",highlightbackground = "white",highlightthickness=3,background ="black",)#"#4C4C4C")
        if background and not self.app.light:
            self.balbg = tk.PhotoImage(file = background)
            self.balbglabel = tk.Label(self.balFrame, image=self.balbg)
            self.balbglabel.place(x=0, y=0, relwidth=1, relheight=1)
        initBal = self.app.wallet.patterns["balance"].search(self.app.wallet.boot)
        if not initBal:
            initBal = ("X.XXXXXXXXXXXX","X.XXXXXXXXXXXX")
            self._root().after(self.app.earliestBalance,self.idle_refresh)
        else:
            try:
                initBal = (initBal.group("balance"),initBal.group("unlocked"))
            except:
                initBal = ("X.XXXXXXXXXXXX","X.XXXXXXXXXXXX")
            self._root().after(25000,self.idle_refresh)
        self.account_picker = MyWidget(self.app,self.balFrame,handle = "Account",cwidth = 21,
                                       choices = self.app.account_menu,startVal = self.app.primary_account,cmd = self.account_chosen)
        self.balLabel = ttk.Label(self.balFrame,text = "Balance:",style = "app.TLabel",)
        self.balance = ttk.Label(self.balFrame,text = initBal[0],style = "app.TLabel",)
        self.unlockedLabel =ttk.Label(self.balFrame,text = "Unlocked:",style = "unlocked.TLabel",)
        self.unlocked = ttk.Label(self.balFrame,text =initBal[1],style = "unlocked.TLabel",)


        self.balLabel.grid(row=1,column=0,sticky=tk.W,padx =(5,0),pady=(5,2))
        self.balance.grid(row=2,column=0,sticky=tk.W,padx =(5,0),pady=(0,2))
        self.unlockedLabel.grid(row=3,column=0,sticky=tk.W,padx =(5,0),pady=(0,2))
        self.unlocked.grid(row=4,column=0,sticky=tk.W,padx =(5,0),pady=(0,5))

        #self.go_send = tk.Button(self.extra,text = "send",command =self.get,image = self.moon3,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#900100" )
        if not self.app.cold:
            self.go_send = tk.Button(self,text = "send",command = self.go_send_event,height = 25,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 5,bg = "red",image = self.bgv,compound = tk.CENTER,cursor = "exchange")
        else:
            self.go_coldsign = tk.Button(self,text = "cold sig",command = self.go_coldsign_event,height = 25,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 5,bg = "skyblue1",image = self.bgv,compound = tk.CENTER,cursor = "exchange")
        self.go_receive = tk.Button(self,text = "receive",command = self.go_receive_event,height = 25,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 5,bg = "green",image = self.bg2,compound = tk.CENTER,cursor = "plus")
        self.go_extras = tk.Button(self,text = "extras",command = self.go_send_event,height = 25,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 5,bg = "blue",image = self.bg3,compound = tk.CENTER,cursor = "trek",state="disabled")
        self.go_donate = tk.Button(self,text = "donate",command = self.go_donate_event,height = 25,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 5,bg = "orange",image = self.bgv,compound = tk.CENTER,cursor = "heart")



        self.showLogo.grid(row=0,column=0,sticky=tk.W)
        self.account_picker.grid(row=0,column=0,padx =(5,0),pady=(5,5),sticky=tk.W+tk.E)
        self.balFrame.grid(row=2,column=0,sticky=tk.W+tk.E)
        if not self.app.cold:
            self.go_send.grid(row=3,column=0,sticky=tk.W+tk.E,pady=(4,0),padx=(4,4))
        else:
            self.go_coldsign.grid(row=3,column=0,sticky=tk.W+tk.E,pady=(4,0),padx=(4,4))
        self.go_receive.grid(row=4,column=0,sticky=tk.W+tk.E,pady=(4,0),padx=(4,4))
        self.go_extras.grid(row=5,column=0,sticky=tk.W+tk.E,pady=(4,0),padx=(4,4))
        self.go_donate.grid(row=6,column=0,sticky=tk.W+tk.E,pady=(4,0),padx=(4,4))

    def go_send_event(self):
        self.app.sendpage.lift()
    def go_coldsign_event(self):
        self.app.coldsignpage.lift()
    def go_receive_event(self):
        self.app.receivepage.lift()
    def go_donate_event(self):
        self.app.donatepage.lift()

    def account_chosen(self):
        try:
            choice = self.account_picker.value.get()
            index = self.app.account_dict[choice]["index"]
            info,bals = self.app.wallet.account_switch(index = index)
            self.balance.configure(text = bals[0])
            self.unlocked.configure(text = bals[1])
            info =  "Currently selected account:\n" + info.split("Currently selected account: ")[-1]
            info = info.replace("Balance: ","Balance:\n").replace(" unlocked balance: ","\nUnlocked:\n")
            self.app.showinfo(info)
        except Exception as e:
            MessageBox.showerror("Account Switch Error",str(e) + "\nUnknown account state. Proceed with caution.")
        finally:
            self.app.receivepage.refresh()

    def refresh_account(self,boot = False,current = None):
        if boot:
            self.app.account_help = self.app.wallet.account_helper(self.app.wallet.boot)
        else:
            result = self.app.wallet.account()
            self.app.account_help = (result[1],result[2])
        print("account help",(self.app.account_help))
        self.app.account_dict = self.app.account_help[0]
        print("account dict",(self.app.account_dict))
        for menu in list(self.app.account_dict.keys()):
            print("account menu",(menu))
            print("account index",self.app.account_dict[menu]["index"])
            if int(self.app.account_dict[menu]["index"]) == 0:
                self.app.primary_account = menu

        self.app.account_menu = self.app.account_help[1]
        self.account_picker.value["values"] = list(self.app.account_menu)
        if not current:
            self.account_picker.value.set(self.app.primary_account)


    def refresh(self):
        if not self.parent.wallet.busy and not self.app.busy:
            now = self.parent.wallet.balance(grandTotal = False)
            self.balance.configure(text = now[0])
            self.unlocked.configure(text = now[1])
            self._root().after(self.delay,self.idle_refresh)
        else:
            self._root().after(5000,self.idle_refresh)
    def idle_refresh(self,something = None):
        self.app.after_idle(self.refresh)


class Statusbar(ttk.Frame):
    def __init__(self,app, parent,delay = 70000,background = "misc/genericspace.gif", *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        if background and not self.app.light:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)
        self.delay = delay
        self.status = ttk.Label(self,text = "Checking Status...",style = "smaller.TLabel")
        self.copyright = tk.Label(self, text = "(c) 2018 u/NASA_Welder",foreground="white", background="black",font=('Liberation Mono','10','normal'))
        self.status.grid(row = 0, column =0,pady=(5,5))
        self.copyright.grid(row = 0, column =1,sticky = tk.E,padx=(80,0))


    def refresh(self,subRefresh = True):
        if not self.parent.wallet.busy:
            now = self.parent.wallet.status(refresh=subRefresh)
            self.status.configure(text = now)
            self._root().after(self.delay,self.idle_refresh)
        else:
            self._root().after(5000,self.idle_refresh)
    def idle_refresh(self,subRefresh = True):
        self._root().after_idle(self.refresh,subRefresh)


class PaneSelect(ttk.Frame):
    def __init__(self,app, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent

class Pane(ttk.Frame):
    def __init__(self,app, parent,background = None,name = None, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        if background and not self.app.light:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)


class Destination(ttk.Frame):
    def __init__(self,app, parent,background = "misc/genericspace3.gif",cwidth = None,select_handle = "Address Book",mode = "send",name = "", *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.name = name
        self.localmenu = None
        self.mode = mode
        if self.mode =="send":
            if not self.app.address_book_menu:
                self.app.address_book = self.app.wallet.address_book()
                self.app.address_book_menu = [""]
                for k,v in self.app.address_book.items():
                    self.app.address_book_menu.append(v["menu"])
                self.app.address_book_menu.sort()
            self.localmenu = self.app.address_book_menu
            self.start = ""
            self.cmd = self.address_book_chosen
        elif self.mode == "receive":
            if not self.app.subaddress_book_menu:
                self.app.subaddress_book = self.app.wallet.address(address_all = True)
                self.app.subaddress_book_menu = []
                largest = 0
                for k,v in self.app.subaddress_book.items():
                    largest = max(largest,int(k))
                    #self.app.subaddress_book_menu.append(v["menu"])
                for i in range(largest+1):
                    self.app.subaddress_book_menu.append(self.app.subaddress_book[str(i)]["menu"])

            self.localmenu = self.app.subaddress_book_menu
            self.start = self.app.subaddress_book_menu[0]
            #print("--------------------------STARTING SUB ADDRESS",self.start)
            self.cmd = self.subaddress_book_chosen
        if self.mode =="donate":
            self.localmenu = [""]
            self.start = ""
            self.cmd = self.do_nothing
        if background and not self.app.light:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)
        self.heading = ttk.Label(self,text = "Address",style = "app.TLabel")
        self.dest_address = tk.Text(self,bg = "white",height = 2,width = 48,insertbackground ="#D15101",selectbackground = "#D15101" )
        self.amount = MyWidget(self.app,self,handle = self.name + "Amount",choices = "entry",)
        self.address_book_select = MyWidget(self.app, self,handle = select_handle,cwidth = cwidth,choices=self.localmenu,startVal = self.start,cmd = self.cmd)

        self.heading.grid(row=0,column=1,sticky = tk.W,pady= (0,0))
        self.dest_address.grid(row=1,column=1,sticky = tk.E,pady= (0,0))
        self.amount.grid(row=0,column=0,rowspan = 2,sticky = tk.NE,pady= (0,0),padx = (0,25))
        if not self.mode =="donate":
            self.address_book_select.grid(row=3,column=0,columnspan = 4,sticky = tk.E,pady= (5,0))
        else:
            self.nasawelder_address = "48Zuamrb7P5NiBHrSN4ua3JXRZyPt6XTzWLawzK9QKjTVfsc2bUr1UmYJ44sisanuCJzjBAccozckVuTLnHG24ce42Qyak6" # u/NASA_Welder
            self.dest_insert(self.nasawelder_address)
            self.dest_address.configure(state='disabled')
        #for windows
        self.address_book_select.bind("<MouseWheel>", self.empty_scroll_command)
        # Linux and other *nix systems
        self.address_book_select.bind("<ButtonPress-4>", self.empty_scroll_command)
        self.address_book_select.bind("<ButtonPress-5>", self.empty_scroll_command)
        if self.mode == "receive":
            self._root().after(100,self.subaddress_book_chosen)
    def empty_scroll_command(self, event):
        return "break"
    def do_nothing(self):
        pass

    def dest_insert(self,address):
        self.dest_address.delete('1.0', tk.END)
        self.dest_address.insert('1.0',address)

    def address_book_chosen(self):
        pick = self.address_book_select.get()[0]
        if pick:
            new_address = self.app.address_book[pick.split(":")[0]]["address"]
            self.dest_insert(new_address)
        else:
            self.dest_insert("")

    def subaddress_book_chosen(self):
        pick = self.address_book_select.get()[0]
        if pick:
            new_address = self.app.subaddress_book[pick.split(":")[0]]["address"]
            self.dest_address.configure(state='normal')
            self.dest_insert(new_address)
            self.dest_address.configure(state='disabled')
            self._root().after(10,self.app.receivepage.genQR)


    def get(self):
        dest = self.dest_address.get("1.0",tk.END).strip()
        amount = self.amount.get()[0]
        try:
            if len(dest) == 95:
                if float(amount) and float(amount) > 0.000000:
                    return dest + " " + amount
        except ValueError as e:
            err = "ERROR in tx #%s"%self.name.split(":")[0] + str(e)
            raise Exception(err)
        return None


class Coldsign(ttk.Frame):
    def __init__(self,app, parent,background = "misc/genericspace2.gif", *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        if False:# self.app.light:
            self.moon3 = tk.PhotoImage(file = "misc/moonbutton3.gif")
            self.cold_transfer_button = tk.Button(self,text = "Sign tx",command =self.do_cold_sign,image = self.moon3,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#900100" )
            self.cold_transfer_button.grid(row=0,column=0,sticky = tk.E,padx = (10,10),pady=(10,10))
        else:
            if background and not self.app.light:
                self.bg = tk.PhotoImage(file = background)
                self.bglabel = tk.Label(self, image=self.bg)
                self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)
            self.heading = ttk.Label(self,text = "Cold Sign",style = "heading.TLabel")
            self.moon3 = tk.PhotoImage(file = "misc/moonbutton3.gif")
            #self.body = VSFrame(self,fheight = 430) # not yet
            self.cold_transfer_button = tk.Button(self,text = "Sign tx",command =self.do_cold_sign,image = self.moon3,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#900100" )

            self.heading.grid(row=0,column=0,sticky = tk.W,pady= (10,15))
            #self.body.grid(row=1,column=0,sticky = tk.W+ tk.E,pady= (5,20))
            self.cold_transfer_button.grid(row=1,column=1,sticky = tk.E,padx = (50,10),pady=(25,0))

    def do_cold_sign(self):
        self.app.outputs_payload = Payload("exoutp",app=self.app,signal_app = True)
        self.app.scanner.add_child(self.app.outputs_payload)
        self.app.preview_request()
        self._root().after(10,self.app.monitor_incoming,self.app.outputs_payload,self.recv_qr_outputs)

    def recv_qr_outputs(self,payload):
        if not self.app.cancel:
            outputs_path = "imported_outputs.lunlumo"
            if payload.toFile(outputs_path):
                self.app.wallet.import_outputs(outputs_path)
                self._root().after(10,self.do_export_key_images)
            else:
                print(repr(payload.bin))
                self.app.showerror("Stopped Automation","Failed crc.\nFailed to reconstruct QR stream: Outputs")

        else:
            self.app.showerror("Stopped Automation","Importing Outputs cancelled upstream.")

    def do_export_key_images(self,):
        if not self.app.cancel:
            key_images_path = "exported_key_images.lunlumo"
            self.app.wallet.export_key_images(key_images_path)
            if not self.app.cancel:
                self.app.sender = SendTop(self.app,self._root(),payloadType="keyimgs",payloadPath = key_images_path)
                self.app.unsigned_tx_payload = Payload("unsgtx",app=self.app,signal_app = True)
                self.app.scanner.add_child(self.app.unsigned_tx_payload)
                self._root().after(10,self.app.monitor_incoming,self.app.unsigned_tx_payload,self.recv_qr_unsigned_tx)
            else:
                self.app.showerror("Stopped Automation","Exporting key images cancelled upstream.")
        else:
            self.app.showerror("Stopped Automation","Exporting key images cancelled upstream.")


    def recv_qr_unsigned_tx(self,payload):
        if not self.app.cancel:
            unsigned_tx_path = "unsigned_%s_tx" % self.app.coin
            if payload.toFile(unsigned_tx_path):
                self.app.wallet.sign_transfer()
                if not self.app.cancel:
                    signed_tx_path = "signed_%s_tx" % self.app.coin
                    self.app.sender = SendTop(self.app,self._root(),payloadType="sigdtx",payloadPath = signed_tx_path)
                    # TODO u/jollymort : should we re-sync outputs/keyimages here?
                else:
                    self.app.showerror("Stopped Automation","sign_transfer cancelled upstream.")
            else:
                print(repr(payload.bin))
                self.app.showerror("Stopped Automation","Failed crc.\nFailed to reconstruct QR stream: unsigned_tx")

        else:
            self.app.showerror("Stopped Automation","sign_transfer cancelled upstream.")
        self.app.preview_cancel()


class Receive(ttk.Frame):
    def __init__(self,app, parent,coin="monero",background = None, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.coin = self.app.coin
        if background and not self.app.light:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)
        self.heading = ttk.Label(self,text = "Receive",style = "heading.TLabel")

        #self.body = VSFrame(self,fheight = 430,nobar = True)
        self.dest = Destination(self.app,self,name = "",cwidth = 40,select_handle = "Subaddress Book",background = "misc/genericspace.gif",mode = "receive")

        self.addresses = []

        #self.textAddress = MyWidget(self.app,self.body.interior,handle = "Address",choices = [self.app.initAddress],cwidth = 50,startVal =  self.app.initAddress )
        self.amountVar = tk.StringVar()
        self.dest.amount.value.config(textvariable = self.amountVar)
        self.new_label = MyWidget(self.app,self,handle = "New Subaddress",ewidth=23,choices = "entry",startVal = "<label goes here>")
        self.moon3 = tk.PhotoImage(file = "misc/moonbutton3.gif")
        self.new_button = tk.Button(self,text = "New Sub.",command =self.new_subaddress,image = self.moon3,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#900100" )
        #self.amount = MyWidget(self.app,self.body.interior,handle = "Amount",choices = "entry",optional = True,activeStart=False)
        #self.amount.value.configure(textvariable = self.amountVar)
        self.amountVar.trace("w", lambda name, index, mode, sv=self.amountVar: self.amountCallback(sv))
        #self.amount.optState.trace("w", lambda name, index, mode, sv=self.amountVar: self.amountCallback(sv))
        self.qr = ttk.Label(self,style = "app.TLabel")
        self.genQR()

        self.heading.grid(row=0,column=0,sticky = tk.W,pady= (10,15))
        #self.body.grid(row=1,column=0,sticky = tk.W+ tk.E,pady= (5,20))
        self.dest.grid(row=1,column=0,columnspan = 2,sticky = tk.W,padx = (15,15))
        self.new_label.grid(row=2,column=0,sticky = tk.W,padx = (109,0),pady=(15,0))
        self.new_button.grid(row=2,column=1,sticky = tk.W,padx = (0,10),pady=(25,0))
        #self.textAddress.grid(row=1,column=0,columnspan = 2,sticky = tk.W)
        #self.amount.grid(row=2,column=1,sticky = tk.E,pady= (10,0))
        self.qr.grid(row=3,column=0,sticky = tk.W+tk.E,padx=(40,0),pady= (15,10),columnspan = 2)

    def new_subaddress(self):
        label = self.new_label.get()[0]
        self.app.wallet.address_new(label = label)
        self.refresh(index = -1)
    def idle_refresh(self,something = None):
        self._root().after_idle(self.refresh)
    def refresh(self,index = 0):
        #self.grid_propagate(False)
        ###
        self.app.subaddress_book = self.app.wallet.address(address_all = True)
        self.app.subaddress_book_menu = []
        largest = 0
        for k,v in self.app.subaddress_book.items():
            largest = max(largest,int(k))
            #self.app.subaddress_book_menu.append(v["menu"])
        for i in range(largest+1):
            self.app.subaddress_book_menu.append(self.app.subaddress_book[str(i)]["menu"])
        ###
        zero = self.app.subaddress_book_menu[index]
        self.dest.address_book_select.value["values"] = list(self.app.subaddress_book_menu)
        self.dest.address_book_select.value.set(zero)
        self.dest.subaddress_book_chosen()
        self.genQR()



    def getAddresses(self):
        addlist = self.app.wallet.address()
        return addlist

    def amountCallback(self,event = None,arg = None):
        #self.grid_propagate(False)
        self._root().after(200,self.genQR)

    def genQR(self):
        msg = self.app.coin + ":" + self.dest.dest_address.get("1.0",tk.END).strip()
        if self.dest.amount.get()[0]:
            try:
                valid = float(self.dest.amount.get()[0])
                msg += "?tx_amount=" + self.dest.amount.get()[0]
            except ValueError as e:
                self.dest.amount.value.delete(0, tk.END)
                MessageBox.showerror("Amount Error",str(e))
        self.qrPage = pyqrcode.create(msg,error="L")
        self.code = tk.BitmapImage(data=self.qrPage.xbm(scale=5))
        self.code.config(background="gray70")
        self.qr.config(image = self.code)


class SendPane(ttk.Frame):
    def __init__(self,app, parent,background = None,delay = 35000, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.delay = delay
        if background and not self.app.light:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)
        self.build_page(background)
    def build_page(self,background):
        self.heading = ttk.Label(self,text = "Send",style = "heading.TLabel")
        self.destFrame = VSFrame(self,fheight = 275)
        self.dests = []
        for i in range(10):
            if i in [1,4,7,]:
                b = "misc/genericspace3.gif"
            elif i in [2,5,8,]:
                b = "misc/genericspace.gif"
            else:
                b = "misc/genericspace2.gif"
            dest = Destination(self.app,self.destFrame.interior,name = "%s: "% str(i+1),background = b)
            dest.pack(padx=(0,20),pady=(0,15))
            self.dests.append(dest)
        #############################
        self.extra = ttk.Frame(self,style = "app.TFrame",)
        self.moon3 = tk.PhotoImage(file = "misc/moonbutton3.gif")
        if background and not self.app.light:
            self.bge = tk.PhotoImage(file = background)
            self.bglabele = tk.Label(self.extra, image=self.bge)
            self.bglabele.place(x=0, y=0, relwidth=1, relheight=1)

        self.payid_title =  ttk.Label(self.extra,text = "Payment ID (optional)",style = "app.TLabel")
        self.payment_id_entry = tk.Text(self.extra,bg = "white",height = 2,width = 33,insertbackground ="#D15101",selectbackground = "#D15101" )
        self.priority = MyWidget(self.app,self.extra,handle = "Priority",choices = ["unimportant","normal","elevated","priority"],startVal = "unimportant")
        self.privacy = MyWidget(self.app,self.extra,handle = "Privacy",choices = [str(i) for i in range(5,51)],startVal = 5)
        self.send_button = tk.Button(self.extra,text = "send",command =self.get,image = self.moon3,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#900100" )

        self.payid_title.grid(row=0,column=1,columnspan=2,sticky = tk.W,)
        self.payment_id_entry.grid(row=1,column=1,columnspan=2,sticky = tk.E)
        self.priority.grid(row=2,column=1,sticky = tk.E,pady=(10,0))
        self.privacy.grid(row=2,column=2,sticky = tk.E,pady=(10,0))
        self.send_button.grid(row=3,column=2,sticky = tk.E,pady=(15,0))
        self.fee_frame = ttk.Frame(self.extra,style = "app.TFrame",width = 200)
        if background and not self.app.light:
            self.bgf = tk.PhotoImage(file = background)
            self.bglabelf = tk.Label(self.fee_frame, image=self.bgf)
            self.bglabelf.place(x=0, y=0, relwidth=1, relheight=1)
        self.fee_title = ttk.Label(self.fee_frame,text = "Backlog / Network Fees",style = "app.TLabel")
        self.cost = ttk.Label(self.fee_frame,text = "<waiting for network fees>",style = "smaller.TLabel")
        self.backlog1 = ttk.Label(self.fee_frame,text = "<waiting for unimportant backlog>",style = "smaller.TLabel")
        self.backlog2 = ttk.Label(self.fee_frame,text = "<waiting for normal backlog>",style = "smaller.TLabel")
        self.backlog3 = ttk.Label(self.fee_frame,text = "<waiting for elevated backlog>",style = "smaller.TLabel")
        self.backlog4 = ttk.Label(self.fee_frame,text = "<waiting for priority backlog>",style = "smaller.TLabel")
        self.fee_title.grid(row=0,column=0,columnspan=1,sticky = tk.W,)
        self.cost.grid(row=1,column=0,columnspan=1,sticky = tk.W,)
        self.backlog1.grid(row=2,column=0,columnspan=1,sticky = tk.W,)
        self.backlog2.grid(row=3,column=0,columnspan=1,sticky = tk.W,)
        self.backlog3.grid(row=4,column=0,columnspan=1,sticky = tk.W,)
        self.backlog4.grid(row=5,column=0,columnspan=1,sticky = tk.W,)
        self.fee_frame.grid(row=0,column=0,columnspan=1,rowspan = 5,sticky = tk.NW,padx=(0,15))

        #############################
        self.heading.grid(row=0,column=0,sticky = tk.W,pady= (10,20))
        self.destFrame.grid(row=1,column=0,columnspan = 3,pady = (0,25),)
        self.extra.grid(row=2,column=0,columnspan = 3,sticky = tk.E,pady=(10,0),padx=(0,15))


    def get(self):
        self.app.cancel = False
        self.app.current_transfer_cmd = ""
        # transfer [index=<N1>[,<N2>,...]] [<priority>] [<ring_size>] <address> <amount> [<payment_id>]
        tx_string = "transfer %s %s" % (self.priority.get()[0],self.privacy.get()[0])
        dest_substring = ""
        try:
            for dest in self.dests:
                result = dest.get()
                if result:
                    dest_substring += " " + result
        except Exception as e:
            MessageBox.showerror("Transaction Error",str(e) )
            return
        if not dest_substring:
            MessageBox.showerror("Transaction Error","No valid destination + amounts found" )
            return
        tx_string += dest_substring
        pay_id = self.payment_id_entry.get("1.0",tk.END).strip()
        if pay_id:
            if not len(pay_id) == 64 or not pay_id.isalnum():
                MessageBox.showerror("Transaction Error","Invalid Payment ID\n\n%s\n\nMust be 64 chars and alphanumeric" % pay_id)
                return
            tx_string += " " + pay_id
        print("Transfer cmd:\n",repr(tx_string))
        if not "Opened watch-only wallet:" in self.app.wallet.boot:
            self.app.wallet.transfer(tx_string)
        else:
            self.app.current_transfer_cmd = tx_string
            outputs_file = "exported_outputs.lunlumo"
            self.app.wallet.export_outputs(outputsFileName = outputs_file)
            self.app.sender = SendTop(self.app,self._root(),payloadType="exoutp",payloadPath = outputs_file,)
            self.app.key_images_payload = Payload("keyimgs",app=self.app,signal_app = True)
            self.app.scanner.add_child(self.app.key_images_payload)
            self.app.preview_request()
            self._root().after(10,self.app.monitor_incoming,self.app.key_images_payload,self.recv_qr_key_images)

    def recv_qr_key_images(self,payload):
        if not self.app.cancel:
            key_images_path = "imported_key_images.lunlumo"
            if payload.toFile(key_images_path):
                self.app.wallet.import_key_images(key_images_path)
                self._root().after(10,self.make_unsigned_tx)
            else:
                self.app.showerror("Stopped Automation","Failed crc.\nFailed to reconstruct QR stream: Key Images")

        else:
            self.app.showerror("Stopped Automation","Importing key images cancelled upstream.")


    def make_unsigned_tx(self,):
        if not self.app.cancel:
            self.app.wallet.transfer(self.app.current_transfer_cmd)
            self.app.current_transfer_cmd = ""
            self.app.sender = SendTop(self.app,self._root(),payloadType="unsgtx",payloadPath = "unsigned_monero_tx",)  # TODO
            self.app.signed_tx_payload = Payload("sigdtx",app=self.app,signal_app = True)
            self.app.scanner.add_child(self.app.signed_tx_payload)
            self._root().after(10,self.app.monitor_incoming,self.app.signed_tx_payload,self.recv_qr_signed_tx)
        else:
            self.app.showerror("Stopped Automation","Making unsigned_tx cancelled upstream.")

    def recv_qr_signed_tx(self,payload):
        if not self.app.cancel:
            signed_tx_path = "signed_%s_tx" % self.app.coin
            if payload.toFile(signed_tx_path):
                self.app.wallet.submit_transfer()
                #self._root().after(10,self.make_unsigned_tx)

            else:
                self.app.showerror("Stopped Automation","Failed crc.\nFailed to reconstruct QR stream: signed_tx")

        else:
            self.app.showerror("Stopped Automation","Submitting transfer cancelled upstream.")
        self.app.preview_cancel()


    def idle_refresh(self,something = None):
        self._root().after_idle(self.refresh)
    def refresh(self):
        self.fee_frame.grid_propagate(False)
        if not self.parent.wallet.busy:
            fee_info = self.app.wallet.fee()
            self.cost.config(text=fee_info[0].replace("Current fee is ",""))
            self.backlog1.config(text=fee_info[1].replace("priority 1","unimportant"))
            self.backlog2.config(text=fee_info[2].replace("priority 2","normal"))
            self.backlog3.config(text=fee_info[3].replace("priority 3","elevated"))
            self.backlog4.config(text=fee_info[4].replace("priority 4","priority"))
        self._root().after(self.delay,self.idle_refresh)

##########################
class Donate(SendPane):
    def __init__(self,app, parent,background = "misc/genericspace3.gif", *args, **kwargs):
        SendPane.__init__(self,app, parent,background = "misc/genericspace3.gif", *args, **kwargs)
        self.app = app
        self.parent = parent

        if background and not self.app.light:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)
        self.build_page(background)
    def build_page(self,background):
        self.heading = ttk.Label(self,text = "Donate",style = "heading.TLabel")
        #self.destFrame = VSFrame(self,fheight = 230)
        self.mydest = Destination(self.app,self,name = "" ,background = "misc/genericspace.gif",mode = "donate")
        self.dests = [self.mydest]

        self.blurb = ttk.Label(self,text = "Thanks for using lunlumo. Continued development is made possible by letting my rugrat play with the kids at daycare. Consider chipping in to the babysitting fund.",style = "app.TLabel",wraplength = 485)
        self.author = ttk.Label(self,text = "- u/NASA_Welder",style = "app.TLabel")

        #############################
        self.extra = ttk.Frame(self,style = "app.TFrame",)
        self.moon3 = tk.PhotoImage(file = "misc/moonbutton3.gif")


        #self.payid_title =  ttk.Label(self.extra,text = "Payment ID (optional)",style = "app.TLabel")
        self.payment_id_entry = tk.Text(self,bg = "white",height = 2,width = 33,insertbackground ="#D15101",selectbackground = "#D15101" )
        self.priority = MyWidget(self.app,self,handle = "Priority",choices = ["unimportant","normal","elevated","priority"],startVal = "unimportant")
        self.privacy = MyWidget(self.app,self,handle = "Privacy",choices = [str(i) for i in range(5,51)],startVal = 5)
        self.send_button = tk.Button(self,text = "send",command =self.get,image = self.moon3,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#900100" )
        self.amountVar = tk.StringVar()
        self.mydest.amount.value.config(textvariable = self.amountVar)
        self.amountVar.trace("w", lambda name, index, mode, sv=self.amountVar: self.amountCallback(sv))

        self.qr = ttk.Label(self,style = "app.TLabel")
        self.genQR()

        #self.payid_title.grid(row=0,column=1,columnspan=2,sticky = tk.W,)
        #self.payment_id_entry.grid(row=1,column=1,columnspan=2,sticky = tk.E)
        #self.priority.grid(row=2,column=1,sticky = tk.E,pady=(10,0))
        #self.privacy.grid(row=2,column=2,sticky = tk.E,pady=(10,0))

        #############################
        self.heading.grid(row=0,column=0,columnspan = 3,sticky = tk.W,pady= (10,15))
        self.mydest.grid(row=3,column=0,columnspan = 3,sticky = tk.NW + tk.E,padx = (30,0),pady = (15,0),)
        self.send_button.grid(row=4,column=2,sticky = tk.N,pady=(20,0),rowspan = 2)
        self.qr.grid(row=5,column=0,sticky = tk.W+tk.E,padx=(10,0),pady= (35,30),columnspan = 2)
        self.blurb.grid(row=1,column=0,sticky = tk.W+tk.E,padx=(5,0),pady= (5,0),columnspan = 3)
        self.author.grid(row=2,column=0,sticky = tk.W+tk.E,padx=(235,0),pady= (0,0),columnspan = 3)
        #self.destFrame.grid(row=1,column=0,columnspan = 3,pady = (0,25),)
        #self.extra.grid(row=2,column=0,columnspan = 3,sticky = tk.E,pady=(10,0),padx=(0,15))

    def amountCallback(self,event = None,arg = None):
        self.grid_propagate(False)
        self._root().after(200,self.genQR)

    def genQR(self):
        msg = "monero" +  ":" + self.mydest.dest_address.get("1.0",tk.END).strip()
        if self.mydest.amount.get()[0]:
            try:
                msg += "?tx_amount=" + str(float(self.mydest.amount.get()[0]))
            except ValueError as e:
                self.mydest.amount.value.delete(0, tk.END)
                MessageBox.showerror("Amount Error",str(e))
        self.qrPage = pyqrcode.create(msg,error="L")
        self.code = tk.BitmapImage(data=self.qrPage.xbm(scale=5))
        self.code.config(background="gray75")
        self.qr.config(image = self.code)
##########################

class FilePicker(ttk.Frame):
    def __init__(self,app, parent,handle,start = None,buttonName = "Select",askPass = False,background = None,ftypes = [("all","*")],idir="./", *args, **kwargs):
        tk.Frame.__init__(self, parent,highlightcolor = "white",highlightbackground = "white",highlightthickness=3,background ="#4C4C4C" , *args, **kwargs)
        self.app = app
        self.parent = parent
        self.handle = handle
        self.ftypes = ftypes
        self.idir = idir
        self.askPass = askPass

        self.moon1 = tk.PhotoImage(file = "misc/moonbutton1.gif")
        self.moon2 = tk.PhotoImage(file = "misc/moonbutton2.gif")
        self.moon3 = tk.PhotoImage(file = "misc/moonbutton3.gif")
        if background:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)

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
        #self.button = ttk.Button(self,text = buttonName,style = "app.TButton",command =self.dialog )
        self.button = tk.Button(self,text = "select",command =self.dialog,image = self.moon2,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#900100" )
        self.title.grid(row = 0,column = 0,padx=(5,0))
        self.button.grid(row = 0,column = 1,padx=6,pady = 6)
        self.select.grid(row = 1,column = 0,sticky = tk.W,columnspan = 3,padx=(5,0),pady=(0,3))
        if self.askPass:
            self.passlbl.grid(row = 2,column = 0,sticky = tk.W,padx=(5,3))
            self.password.grid(row = 2,column = 1,sticky = tk.W,padx=(0,7),pady = (0,8))

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
    def __init__(self,app, parent,background = None,*args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.final = None

        self.moon1 = tk.PhotoImage(file = "misc/moonbutton1.gif")
        self.moon2 = tk.PhotoImage(file = "misc/moonbutton2.gif")
        self.moon3 = tk.PhotoImage(file = "misc/moonbutton3.gif")
        if background:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)

        self.logo = tk.PhotoImage(file = "misc/reddit_user_philkode_made_this.gif")
        self.showLogo = ttk.Label(self,image= self.logo,style = "app.TLabel",cursor = "shuttle")
        #heading = ttk.Label(first,text= "Wallet Options",style = "app.TLabel")
        self.walletFile = FilePicker(self.app,self,"wallet file",askPass = True,start = None,background = "misc/genericspace.gif",ftypes = [("full","*.keys"),("watchonly","*.keys-watchonly")],idir="./")
        self.testnet = MyWidget(self.app,self,handle = "testnet",optional = 1,)
        self.launch = tk.Button(self,text = "launch!",command =self.launch,cursor = "shuttle",image = self.moon3,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#900100" )
        #MyWidget(app, parent,handle,choices=None,subs = {},allowEntry = False,optional = False,activeStart=1,ewidth = 8,cwidth = None, cmd = None)
        self.daemon = MyWidget(self.app,self,handle = "daemon",startVal = "None (cold wallet)",allowEntry = False,cwidth = 18,cipadx = 1,
                                choices = ["None (cold wallet)","local, already running","other, host[:port]",],
                               subs={"other, host[:port]":{"handle":"host[:port]","choices":"entry","ewidth":20,"allowEntry":False},}) # allow Entry not applicable
        self.camera_choice = MyWidget(self.app,self,handle = "camera",startVal = "None",allowEntry = False,cwidth = 18,cipadx = 1,
                                choices = ["None","webcam (v4l)","raspi cam",])

        self.showLogo.grid(row=0,column=0,rowspan=1,columnspan=2,sticky = tk.E)
        #self.heading.grid(row=0,column=1,sticky=tk.W)
        self.walletFile.grid(row=1,column=0,pady=(5,0),columnspan=2,sticky = tk.W+tk.E)
        self.daemon.grid(row=2,column=0,pady=(10,0),rowspan=1,columnspan=2)
        self.camera_choice.grid(row=3,column=0,pady=(10,15),rowspan=1,columnspan=2)
        self.testnet.grid(row=4,column=0,padx=(5,0),pady=10)
        self.launch.grid(row=4,column=1,padx=(5,0),pady= 5)

    def launch(self):
        wallet = self.walletFile.get()
        vals = {"walletFile": wallet[0],"password": wallet[1],"camera_choice":self.camera_choice.get()[0],"testnet":bool(self.testnet.get()),}
        print("login",repr(vals))
        daemon = self.daemon.get()
        if daemon[0] == "None (cold wallet)":
            vals.update({"cold":True})
        elif  daemon[0] == "local, already running":
            vals.update({"cold":False})
        elif daemon[0] == "other, host[:port]":
            both = daemon[1].split(":")
            host = daemon[1].split(":")[0]
            if len(both)==1:
                vals.update({"daemonHost":daemon[1]})
                vals.update({"cold":False})
            elif len(both) == 2:
                port = daemon[1].split(":")[1]
                vals.update({"daemonAddress":host + ":" + port})
                vals.update({"cold":False})
            else:
                MessageBox.showerror("Login Error","Could not parse daemon host[:port]\n\ne.x. testnet.xmrchain.net\n\ne.x. testnet.xmrchain.net:28081")
                return

        self.final = vals
        self.app.destroy()


class MyWidget(ttk.Frame):
    def __init__(self,app, parent,handle,choices=None,subs = {},startVal = None,allowEntry = False,static = False, background = "misc/genericspace.gif",
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

        if False:# background and not self.app.light:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)

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
            self.value = ttk.Combobox(self,values = self.choices,state = state,width=cwidth,postcommand = self.wideMenu,style = "app.TCombobox")
            self.value.bind('<<ComboboxSelected>>',self.findSubs)
            #self.value.bind('<Configure>', self.wideMenu)
        if self.choices == "entry":
            state = "enabled" if not static else "readonly"
            self.value = ttk.Entry(self,width=ewidth,style = "app.TEntry",state = state)
            self._root().after(0,self.findSubs,None,False)

        self.title = ttk.Label(self, text = self.handle,style = "app.TLabel")
        self.title.pack(anchor = tk.W)
        if self.choices:
            self.value.pack(anchor = tk.E,ipadx = cipadx)
            if not self.startVal is None:
                if not self.choices == "entry":
                    self.value.set(self.startVal)
                    self._root().after(0,self.findSubs,None,False)
                else:
                    self.value.insert(0,startVal)
                    self._root().after(0,self.findSubs,None,False)
        if self.optional:
            if activeStart:
                self.optState.set(1)

    def wideMenu(self,event = None):
        try:
            global mystyle
            if self.handle in ["Account"]:
                #print("got Account wideMenu")
                mystyle.configure("TCombobox",postoffset = (0,0,150,0))
                self.value.config(style = "TCombobox")
            elif self.handle in ["Subaddress Book"]:
                mystyle.configure("TCombobox",postoffset = (0,0,100,0))
                self.value.config(style = "TCombobox")
            else:
                mystyle.configure("TCombobox",postoffset = (0,0,0,0))
        except Exception as e:
            print(str(e))


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
        else:
            print("someone tried to get:%s" %self.handle)
            return #[self.value.get()]

    def findSubs(self,event = None,not_init = True):
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
        if self.cmd and not_init:
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


################
class Preview(tk.Toplevel):
    def __init__(self,app,parent,delay = 450*3,title="Scanner",*args,**kargs):
        tk.Toplevel.__init__(self,background = "black")
        self.app = app
        self.parent = parent
        self._title = title
        self.title(self._title)
        self.delay = delay

        self.preview_screen = tk.Label(self)
        self.preview_screen.pack()
        self.status_display = tk.Label(self,text = "waiting for codes")
        self.status_display.pack()
        self.status2 = tk.Label(self,text = "waiting for codes",wraplength = 250)
        self.status2.pack()
        self.protocol("WM_DELETE_WINDOW", self.kill)

        w, h = self._root().winfo_screenwidth(), self._root().winfo_screenheight()
        self.geometry("256x%d+%d+%d" % (int(256*480/640+20),int(0),int(h-256*480/640+20)))
        #self.lift()
        self.showme()
        self._root().after(self.delay,self.get_preview)

    def get_preview(self):
        thumb = self.app.scanner.snapshot()
        if thumb:
            print("making thumb label")
            self.img = ImageTk.PhotoImage(thumb)
            self.preview_screen.config(image = self.img)
            try:
                stat = [i+1 for i,v in enumerate(self.app.scanner.children[0].bin) if v ==0]
                self.status2.configure(text=repr(stat))
            except Exception as e:
                print(str(e))
        self._root().after(self.delay,self.get_preview)
        self.attributes('-topmost', 1)

    def digest(self,codes):
        if codes:
            self.status_display.config(text = "found:  " + codes[0].split(":")[0])
        else:
            self.status_display.config(text = "<nothing found>")


    def showme(self):
        #self.grab_set()
        #self.focus()
        #w, h = self._root().winfo_screenwidth(), self._root().winfo_screenheight()
        #print("w:",w,",h:",h)
        #self.geometry("%dx%d+0+0" % (w, h))
        self.lift()
        self.attributes('-topmost', 1)

        #self._root().after(200,self.attributes,'-topmost', 0)
        #self._root().after(210,self._root().attributes,'-topmost', 1)
        #self._root().after(220,self._root().attributes,'-topmost', 0)

        #self._root().after(100,self.geometry,"%dx%d+0+0" % (int(w*.9), h))
        #self.lift()


        #self.attributes('-fullscreen', True)
    def kill(self):
        print("Preview '%s' closed by WM_DELETE_WINDOW" % self._title)
        self.app.preview_cancel()
    def close(self):
        print("Preview '%s' closed" % self._title)
        self.destroy()






class SendTop(tk.Toplevel):
    def __init__(self,app,parent,title="File Sender",*args,**kargs):
        tk.Toplevel.__init__(self,background = "black")
        self.app = app
        self.parent = parent
        self._title = title
        self.title(self._title)
        self.sender = SendFrame(self.app,self, *args,**kargs)

        self.protocol("WM_DELETE_WINDOW", self.close)

        self.sender.pack(anchor = tk.W)
        w, h = self._root().winfo_screenwidth(), self._root().winfo_screenheight()
        self.geometry("%dx%d+%d+0" % (int(w*.85), h,int(w*.14)))
        #self.lift()
        self.showme()

    def showme(self):
        #self.grab_set()
        #self.focus()
        #w, h = self._root().winfo_screenwidth(), self._root().winfo_screenheight()
        #print("w:",w,",h:",h)
        #self.geometry("%dx%d+0+0" % (w, h))
        self.lift()
        self.attributes('-topmost', 1)

        #self._root().after(200,self.attributes,'-topmost', 0)
        #self._root().after(210,self._root().attributes,'-topmost', 1)
        #self._root().after(220,self._root().attributes,'-topmost', 0)

        #self._root().after(100,self.geometry,"%dx%d+0+0" % (int(w*.9), h))
        #self.lift()


        #self.attributes('-fullscreen', True)
    def close(self):
        print("SendTop '%s' closed by WM_DELETE_WINDOW" % self._title)
        self._root().after(10,self.destroy)

class SendFrame(tk.Frame):
    def __init__(self,app,parent,payloadType,payloadPath,PAGE_SIZE = 700,qrBackground = "gray52",qrForeground = "gray1",qrScale = 8,delay = 850,width = 350, height = 400,*args,**kargs):
        tk.Frame.__init__(self,parent,height = height,background = "black", width = width, *args,**kargs) # style = "app.TFrame"
        #global slides
        self.app = app
        self.checksum = crc(payloadPath)
        self.skip = []
        self.delay = delay
        self.PAGE_SIZE = PAGE_SIZE
        self.payloadType = payloadType
        self.payloadPath = payloadPath
        self.qrScale = qrScale
        self.qrBackground = qrBackground
        self.qrForeground = qrForeground
        ##################################
        # settings
        self.moon = tk.PhotoImage(file = "misc/moonbutton1.gif")
        self.settings = tk.Frame(self,background = "black")
        self.title = ttk.Label(self,text = "sending: %s" % (os.path.basename(payloadPath)),style = "app.TLabel")
        self.crclbl = ttk.Label(self,text = "crc32: %s" % self.checksum,style = "app.TLabel")
        self.ticker = ttk.Label(self,text = "X / X",style = "app.TLabel")

        self.bytesEntry = MyWidget(self.app,self.settings,handle = "bytes / QR",choices="entry",startVal = self.PAGE_SIZE)
        self.scaleEntry = MyWidget(self.app,self.settings,handle = "size",choices=[str(x) for x in range(4,15)],startVal = self.qrScale)
        self.bgEntry = MyWidget(self.app,self.settings,handle = "bg color",choices=["gray" + str(x) for x in range(1,100)],allowEntry = 1,startVal = self.qrBackground)
        self.fgEntry = MyWidget(self.app,self.settings,handle = "fg Color",choices=["gray" + str(x) for x in range(1,100)],allowEntry = 1,startVal = self.qrForeground)
        self.delayEntry = MyWidget(self.app,self.settings,handle = "delay (ms)",choices="entry",startVal = self.delay)
        self.resetButton = tk.Button(self.settings,text = "apply",command =self.reset,image = self.moon,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "light gray",bd = 3,bg = "#900100" )

        self.title.grid(row=0,column = 0,sticky=tk.W)
        self.crclbl.grid(row=1,column = 0,sticky=tk.W,)
        self.ticker.grid(row=1,column = 2,sticky=tk.W,padx=(0,20))

        self.bytesEntry.grid(row = 0,column = 0,sticky = tk.E)
        self.scaleEntry.grid(row = 1,column = 0,sticky = tk.E)
        self.bgEntry.grid(row = 2,column = 0,sticky = tk.E)
        self.fgEntry.grid(row = 3,column = 0,sticky = tk.E)
        self.delayEntry.grid(row = 4,column = 0,sticky = tk.E)
        self.resetButton.grid(row = 5,column = 0,pady=(10,0))
        ##################################
        # Create QR images
        self.slides = []
        self.codes = []
        with open(payloadPath, "rb") as source:
            self.payload = base64.b64encode(source.read())

        self.numQR = ceil(len(self.payload)/self.PAGE_SIZE)
        if self.numQR >= 1000:
            raise Exception("%s QRs!! file really got out of hand, exiting"% self.numQR)

        self.ind = 0
        self.i = 1
        self.x = 0

        self.ready = False
        self.make_slides()
        self._root().after(50, self.idle_refresh,)

        #################################


        self.current = ttk.Label(self,style = "app.TLabel")

        self.settings.grid(row=2,column = 0,sticky=tk.NW,padx = (0,30))

        self.current.grid(row=0,column = 3,rowspan =9,sticky=tk.W)

    def reset(self):
        self.delay = int(self.delayEntry.get()[0])
        self.PAGE_SIZE = int(self.bytesEntry.get()[0])
        self.qrScale = int(self.scaleEntry.get()[0])
        self.qrBackground = self.bgEntry.get()[0]
        self.qrForeground = self.fgEntry.get()[0]

        self.numQR = ceil(len(self.payload)/self.PAGE_SIZE)
        if self.numQR >= 1000:
            raise Exception("%s QRs!! file really got out of hand, exiting"% self.numQR)
        self.slides = []
        self.skip = []
        self.i = 1
        self.x = 0
        self.ind = 0
        if self.ready: self.make_slides()
        self.ind = 0


    def make_slides(self):
        chunk = self.payload[self.x: self.x+self.PAGE_SIZE]
        if chunk:
            self.ready = False
            heading = self.payloadType + "," + self.checksum + "," + str(self.i) + "/" + str(int(self.numQR)) + ":"
            page = heading + b(chunk)
            qrPage = pyqrcode.create(page,error="L")
            #saved = qrPage.svg(heading.replace(",","_").replace(":","_").replace("/","_") + ".svg")
            code = tk.BitmapImage(data=qrPage.xbm(scale=self.qrScale))
            code.config(background=self.qrBackground,foreground = self.qrForeground )
            #exec("self.i%s = code"% self.i)
            self.slides.append(code)
            self.i+=1
            self.x += self.PAGE_SIZE
            self._root().after(100, self.make_slides)
        else:
            self.ready = True
    def idle_refresh(self,something = None):
        self._root().after_idle(self.refresh)
    def refresh(self):
        print("refresh :" ,self.ind)
        if self.slides:
            while self.ind in self.skip:
                print("skipping :",self.ind)
                self.ind += 1
            try:
                slide = self.slides[self.ind]
                self.ticker.configure(text = "%s / %s" % (self.ind+1,self.numQR))
                print("showing :",self.ind)
                self.current.configure(image=slide)
            except IndexError:
                self.ind = 0
                print("indexError :",self.ind)
            else:
                self.ind += 1
            if self.ind >= self.numQR:
                print("end reached :",self.ind)
                self.ind =0

        self._root().after(self.delay, self.idle_refresh,)

"""
# here be dragons
class MyConfirm(SimpleDialog):

    def body(self, master):


        self.bgb = tk.PhotoImage(file = "misc/genericspace.gif")
        self.bglabelb = tk.Label(self.body, image=self.bgb)
        self.bglabelb.place(x=0, y=0, relwidth=1, relheight=1)
        Label(master, text="First:").grid(row=0)
        Label(master, text="Second:").grid(row=1)

        self.e1 = Entry(master)
        self.e2 = Entry(master)

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        return self.e1 # initial focus

    def apply(self):
        first = int(self.e1.get())
        second = int(self.e2.get())
        print(first, second) # or something
"""

# http://tkinter.unpythonic.net/wiki/VerticalScrolledFrame
class VSFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent,fheight = 200, nobar = False, background = "misc/genericspacev.gif",*args, **kw):
        tk.Frame.__init__(self, parent,bg = "black", *args, **kw)
        if background and not self.app.light:
            self.bgf = tk.PhotoImage(file = background)
            self.bglabelf = tk.Label(self, image=self.bgf)
            self.bglabelf.place(x=0, y=0, relwidth=1, relheight=1)
        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        if not nobar:
            vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set,height = fheight,background = "black")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)
        if background and not self.app.light:
            self.bgc = tk.PhotoImage(file = background)
            self.bglabelc = tk.Label(canvas, image=self.bgc)
            self.bglabelc.place(x=0, y=0, relwidth=1, relheight=1)
        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas,bg = "black")
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)
        if background and not self.app.light:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self.interior, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)







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
        code.config(background="gray55")
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

"""
Noto Sans Ogham
OpenSymbol
Noto Sans Lepcha
Noto Serif Thai
Noto Sans Javanese
DejaVu Sans Mono
Noto Sans Cherokee
KacstTitleL
Noto Sans Syriac Eastern
DejaVu Sans
Liberation Mono
Liberation Mono
Liberation Mono
Noto Sans Meetei Mayek
Noto Sans Symbols
Ubuntu
Tlwg Typo
"""


if __name__ == "__main__":

    first = tk.Tk()

    first.configure(bg="#F2681C")
    first.geometry("%dx%d%+d%+d" % (400, 530, 300, 150))  #(width, height, xoffset, yoffset)
    bg = tk.PhotoImage(file = "misc/genericspace.gif")
    bglabel = tk.Label(first, image=bg)
    bglabel.bgimage = bg
    bglabel.place(x=0, y=0, relwidth=1, relheight=1)

    #first.option_add('*TCombobox*Listbox.font', ('Liberation Mono','8','normal'))
    #first.option_add('*TCombobox*Entry.font', ('Liberation Mono','8','normal'))
    first.title("lunlumo (login)")
    mystyle = ttk.Style()
    mystyle.theme_use('clam') #('clam', 'alt', 'default', 'classic')
    mystyle.configure("app.TLabel", foreground="white", background="black", font=('Liberation Mono','10','normal')) #"#4C4C4C")
    mystyle.configure("heading.TLabel", foreground="white", background="black",) #"#4C4C4C")
    mystyle.configure("app.TFrame", foreground="gray55", background="#4C4C4C",)
    mystyle.configure("app.TButton", foreground="gray55", background="#C6480E",activeforeground ="#F2681C",font=('Liberation Mono','10','normal'),height = 5  )#F2681C
    mystyle.configure("app.TCheckbutton", foreground="gray55", background="black") #"#4C4C4C")
    mystyle.configure("app.TCombobox", background="#F2681C",font=('Liberation Mono','12','normal'))#,selectbackground = "#D15101",fieldbackground = "#D15101")
    mystyle.configure("app.TEntry", foreground="black", background="gray55",font=('Liberation Mono','12','normal'))
    mystyle.configure("pass.TEntry", foreground="gray55", background="gray55",insertofftime=5000)
    first.option_add("*TCombobox*Listbox*selectBackground", "#D15101")
    login = Login(first,first,background = "misc/genericspace.gif")
    login.pack()

    first.mainloop()

    #################################
    if login.final:
        root = tk.Tk()
        #root.geometry("%dx%d%+d%+d" % (800, 500, 300, 150))  #(width, height, xoffset, yoffset)
        root.title("lunlumo")
        mystyle = ttk.Style()
        bgr = tk.PhotoImage(file = "misc/genericspace2.gif")
        bglabelr = tk.Label(root, image=bgr)
        bglabelr.bgimage = bgr
        bglabelr.place(x=0, y=0, relwidth=1, relheight=1)
        mystyle.theme_use('clam') #('clam', 'alt', 'default', 'classic')
        mystyle.configure("app.TLabel", foreground="white", background="black",font=('Liberation Mono','12','normal')) #"#4C4C4C")
        mystyle.configure("unlocked.TLabel", foreground="light green", background="black",font=('Liberation Mono','12','normal')) #"#4C4C4C")
        mystyle.configure("smaller.TLabel", foreground="white", background="black",font=('Liberation Mono','10','normal')) #"#4C4C4C")
        mystyle.configure("heading.TLabel", foreground="white", background="black",font=('Liberation Mono','36','normal')) #"#4C4C4C")
        mystyle.configure("app.TFrame", foreground="gray55", background="black")#"#4C4C4C",)
        mystyle.configure("app.TButton", foreground="gray55", background="#D15101",activeforeground ="#F2681C")#F2681C
        mystyle.configure("app.TCheckbutton", foreground="gray55", background="black") #"#4C4C4C")
        mystyle.configure("app.TCombobox", background="#F2681C",selectbackground = "#D15101") #postoffset = (0,0,500,0))
        mystyle.configure("app.TEntry", foreground="black", background="gray55")
        mystyle.configure("pass.TEntry", foreground="gray55", background="gray55",insertofftime=5000)
        root.option_add("*TCombobox*Listbox*selectBackground", "#D15101")
        try:
            App = Lunlumo(root,root,cmd = sys.argv[1],**login.final)
        except Exception as e:
            print(str(e))
            MessageBox.showerror("Wallet Error",str(e))
            raise
        else:
            App.pack()#grid(row=0,column=0)

        root.mainloop()

        App.wallet.stopWallet()


    ########################################################

    sys.exit(0)

    # this was the old way \/
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

