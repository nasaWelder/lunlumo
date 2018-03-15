# interface.py explanation of how to interface via QR code with lunlumo - not meant to be run as code. .py file for syntax highlighting
# Copyright (C) 2018  u/NASA_Welder
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

raise Exception("this file is not meant to be run, just a collection of pseudocode. It is '.py' for syntax highlighting only")

"""
QR code format: <memo>,<crc32>,<m>/<n>:<base64 encoded file snippet>
       example: exoutp,984731a5,5/20:TW9uZXJvIG91dHB1dCBleHBvcnQDG8Eyv9d42cIhIpzYDRYM6jstEv6cFnjlPD2+Y045t7ftnVkyqaTJeG

Since lunlumo expects the  file snippets to be base64 encoded according to the python standard library "base64", 3rd party apps must use that library's algorithm

"memo" needs to be hardcoded/precoordinated between sender/receiver in most cases, such as when automating a multi step process
so that receiver will know it is capturing the correct file for its intended purpose.

The crc32 of transferred file should be checked by receiver against crc32 found in header to ensure file integrity, otherwise process should abort.
"""

# encoding a file as base64 in python
import base64
with open(payloadPath, "rb") as source:
    encoded_file = base64.b64encode(source.read())


# crc32 as calculated in python:
# NOTE: I have seen crc32 of length 7 in the wild so don't hardcode length of crc in parsing logic
import zlib
def crc(fileName):
    prev = 0
    for eachLine in open(fileName,"rb"):
        prev = zlib.crc32(eachLine, prev)
    return "%x"%(prev & 0xFFFFFFFF)


# generating QR codes example.
# I've removed most of the displaying of the codes below to give a rough outline.
# (in lunlumo, the generation and display is intertwined)
# see lunlumo.py for actual code
import re
import math
import base64
import pyqrcode
class SendFrame(object):
    def __init__(self,payloadType,payloadPath,PAGE_SIZE = 700,qrBackground = "gray52",qrForeground = "gray1",qrScale = 8,delay = 850,width = 350, height = 400,*args,**kargs):

        self.checksum = crc(payloadPath)

        ###############
        # for an an optional feature, yet to be tested, that will allow skipping over slides
        # the reciever has indicated as already scanned. (a speed optimization)
        self.status_pattern = re.compile("client_status" + r",(?P<crc>[a-z0-9]{7,10}),(?P<rank>[0-9]{1,5})/(?P<total>[0-9]{1,5}):(?P<payload>\S+)")
        self.skip = set([])
        ###############

        self.payloadType = payloadType
        self.payloadPath = payloadPath

        self.PAGE_SIZE = PAGE_SIZE
        self.qrScale = qrScale
        self.qrBackground = qrBackground
        self.qrForeground = qrForeground
        self.delay = delay

        # Create QR images
        self.slides = [] # container for sequential QR codes
        # encode whole file before splitting
        with open(payloadPath, "rb") as source:
            self.payload = base64.b64encode(source.read())

        # self imposed sanity check that may go away
        self.numQR = math.ceil(len(self.payload)/self.PAGE_SIZE)
        if self.numQR >= 10000:
            raise Exception("%s QRs!! file really got out of hand, exiting"% self.numQR)

        self.ind = 0
        self.i = 1
        self.x = 0

        self.ready = False
        while not self.ready:
            self.make_slides()

    def make_slides(self):
        chunk = self.payload[self.x: self.x+self.PAGE_SIZE] #make a snippet
        if chunk: # in python a slice is empty if it goes out of bounds, not an error. your language may require kid gloves to know when you're done.
            self.ready = False
            heading = self.payloadType + "," + self.checksum + "," + str(self.i) + "/" + str(int(self.numQR)) + ":" # the lunlumo header format
            page = heading + b(chunk) # test to go into QR
            qrPage = pyqrcode.create(page,error="L") # using lowest error correction setting so more data can fit

            code = tk.BitmapImage(data=qrPage.xbm(scale=self.qrScale)) # in python this actually creates the image itself. Your language will differ
            code.config(background=self.qrBackground,foreground = self.qrForeground )

            self.slides.append(code)
            self.i+=1 # increase "m" in "m/n" format for heading
            self.x += self.PAGE_SIZE # increment starting point for next snippet
        else:
            self.ready = True # reached end of file, jump out of while loop.
    ############################################
    #optional speed optimization feature, untested
    # digest would be called externally by QR code scanner
    def digest(self,codes):
        for code in codes:
            try:
                match = self.status_pattern.fullmatch(code)
                if match:
                    if match.group("crc") == self.checksum:
                        self.skip = eval(match.group("payload")) | self.skip
            except:
                pass
    #############################################
    #############################################
    #############################################


# receiving / stitching together a file
import re
class Payload(object):
    def __init__(self,msgType,scanner = None,app = None,signal_app = False,verbose=False):
        self.verbose = verbose
        self.msgType = msgType
        self.app = app
        self.signal_app = signal_app # Optional:  a function to signal parent app so that it will stop displaying previous send loop because now we have a response
        self.pattern = re.compile(self.msgType + r",(?P<crc>[a-z0-9]{7,10}),(?P<rank>[0-9]{1,5})/(?P<total>[0-9]{1,5}):(?P<payload>\S+)") # will find a valid lunlumo file snippet
        self.bin = [] # container for found/matching QRs
        self.total = None # max number of QRs found in header

    def _use(self,match):
        index = int(match.group("rank")) - 1
        self.bin[index] = match.group("payload")
        #if self.verbose: print("found:",index)


    def grab(self,still):
        codes = zbarlight.scan_codes('qrcode', still)
        if codes:
            codes = [b(i) for i in codes]
            self.digest(codes)

    def digest(self,codes):
        # this function, at least in lunlumo is calle by QR code scanner object. You can change how/when you call it
        if not self.bin:
            for code in codes:
                match = self.pattern.fullmatch(code)
                if match:
                    if self.app and self.signal_app: # if we want to signal parent app...
                        try:
                            self.app.payload_started()
                        except Exception as e:
                            print(str(e))
                    self.total = match.group("total")
                    self.bin = [0 for i in range(int(self.total))] # create an "empty" "array" for external status monitor to know when wwe are done
                    self.crc = match.group("crc")

                    self._use(match)
                    self.pattern = re.compile(self.msgType + "," + self.crc + r",(?P<rank>[0-9]{1,5})/(?P<total>[0-9]{1,5}):(?P<payload>\S+)")
                    break
                else:
                    print("got unexpected QR: %s" % code) # just debug code

        else:
            for code in codes:
                match = self.pattern.fullmatch(code)
                if not match.group("total") == self.total: # host has reset codes, with different bytes / QR, so discard current file #TODO if we can salvage the existing data, could be a speed up. would need like byte index (start,size,total)
                    self.reset(match = match)

                if match:
                    self._use(match)
    def got_all(self):
        # called externally by parent app every few seconds to see if all QRs have been found
        if self.bin:
            if not 0 in self.bin: # if all QR codes have been found
                return True
        return False

    def stitched(self):
        if self.got_all():
            return "".join(i for i in self.bin).strip() # concatenate all the snippets in order
        else:
            raise Exception("Payload Error: Payload was not ready to be stitched\n%r" % self.bin)

    def prepared(self):
        finished = base64.b64decode(self.stitched()) # decode file back into binary (i think it's binary)

        # debugging calc of crc32
        prev = 0
        prev = zlib.crc32(finished, prev)
        text_crc = "%x"%(prev & 0xFFFFFFFF)

        return finished, bool(self.crc == text_crc)

    def toFile(self,path):
        # write received file to path
        # called externally when parent app realizes that all QR codes have been found

        data, success = self.prepared()
        with open(path, 'wb') as dest:
            dest.write(data)
        # calce crc32 of final file to make sure successfultransfer, but let parent app handle True/False
        prev = 0
        for eachLine in open(path,"rb"):
            prev = zlib.crc32(eachLine, prev)
        actual_crc = "%x"%(prev & 0xFFFFFFFF)
        return bool(self.crc == actual_crc) # let parent handle whatever happens



    def reset(self,match=None,hard = False):
        # if user on sender side changes bits/ QR need to throw out existing codes (for now, there is probably a way to repackage existing found data and not destroy it)
        self.bin = []
        self.total = None
        if hard: # if we want to throw out crc also, meaning new file incoming (not used yet)
            self.pattern = re.compile(self.msgType + r",(?P<crc>[a-z0-9]{8}),(?P<rank>[0-9]{1,5})/(?P<total>[0-9]{1,5}):(?P<payload>\S+)")
        if match:
            self.total = match.group("total")
            self.bin = [0 for i in range(int(self.total))]
            #self.crc = match.group("crc")
            #self.pattern = re.compile(self.msgType +  "," + self.crc + r",(?P<rank>[0-9]{1,5})/(?P<total>[0-9]{1,5}):(?P<payload>\S+)")


# Example cold signing hot wallet work flow including precoordinated memos
class App_subset(object): # juist a tiny subset of the parent app.
    def __init__(self):
        self.wallet = wex.Wallet(walletFile, password,daemonAddress, daemonHost,testnet,self.cold,gui=self,postHydra = True,debug = 0,cmd = cmd,coin = self.coin)
        if camera_choice == "webcam (v4l)":
            from scanner import Scanner_pygame
            self.scanner = Scanner_pygame(app = self)

    def monitor_incoming(self,payload,when_finished,*args,**kwargs):
        if not payload.got_all():
            self._root().after(2000,self.monitor_incoming,payload,when_finished,*args,**kwargs) # schedule next check in the future
        else:
            self.scanner.children.remove(payload)
            self._root().after(50,when_finished,payload,*args,**kwargs) # do the callback that was supplied when File done receiving

class Hot_Wallet_Side_of_Things(object):
    def __init__(self,app):
        self.app = app # just a reference to parent app, and it's functions
    def hot_wallet_cold_sign(tx_string)
        self.app.current_transfer_cmd = tx_string
        try:
           t = time.gmtime()
           outputs_file = "exported_outputs_%s%s%s%s%s.lunlumo"% (t[0],t[7],t[3],t[4],t[5])
        except:
           outputs_file = "exported_outputs.lunlumo"
        self.app.wallet.export_outputs(outputsFileName = outputs_file) # monero wallet exports wallet to desired filename
        # NOTE the payloadType="exoutp" below, that's the precoordinated memo you need to use
        self.app.sender = SendTop(self.app,self._root(),payloadType="exoutp",payloadPath = outputs_file,) # Sender is a display wrapper arround SendFrame
        self.app.key_images_payload = Payload("keyimgs",app=self.app,signal_app = True) # an object to store next file to be recieved
        self.app.scanner.add_child(self.app.key_images_payload) # so scanner can feed QRs it finds to the payload

        self._root().after(10,self.app.monitor_incoming,self.app.key_images_payload,self.recv_qr_key_images) # schedule the parent app to start checking for incoming key images

    def recv_qr_key_images(self,payload):
        # callback called after key images are received
        if not self.app.cancel: # an way for the parent app to abort
            try:
               t = time.gmtime()
               key_images_path =  "imported_key_images_%s%s%s%s%s.lunlumo"% (t[0],t[7],t[3],t[4],t[5])
            except:
               key_images_path = "imported_key_images.lunlumo"
            if payload.toFile(key_images_path):
                self.app.wallet.import_key_images(key_images_path) #monero wallet imports the key images
                self._root().after(10,self.make_unsigned_tx)   # schedule the next part of the process to start in 10 ms
            else:
                self.app.showerror("Stopped Automation","Failed crc.\nFailed to reconstruct QR stream: Key Images")

        else:
            self.app.showerror("Stopped Automation","Importing key images cancelled upstream.")


    def make_unsigned_tx(self,):
        if not self.app.cancel:
            self.app.wallet.transfer(self.app.current_transfer_cmd) # monero wallet makes unsigned tx
            self.app.current_transfer_cmd = "" # clear transfer command just in case
            if not self.app.cancel:
                self.app.sender = SendTop(self.app,self._root(),payloadType="unsgtx",payloadPath = "unsigned_monero_tx",)  # TODO when will aeon change file name? u/stoffu
                self.app.signed_tx_payload = Payload("sigdtx",app=self.app,signal_app = True)
                self.app.scanner.add_child(self.app.signed_tx_payload)
                self._root().after(10,self.app.monitor_incoming,self.app.signed_tx_payload,self.recv_qr_signed_tx)
            else:
                self.app.showerror("Stopped Automation","Sending unsigned_tx cancelled upstream.")
        else:
            self.app.showerror("Stopped Automation","Making unsigned_tx cancelled upstream.")

    def recv_qr_signed_tx(self,payload):
        if not self.app.cancel:
            signed_tx_path = "signed_%s_tx" % "monero" #self.app.coin # TODO u/stoffu when aeon change file name?
            if payload.toFile(signed_tx_path):
                self.app.wallet.submit_transfer() # monero wallet actually send the funds
                #self._root().after(10,self.make_unsigned_tx)

            else:
                self.app.showerror("Stopped Automation","Failed crc.\nFailed to reconstruct QR stream: signed_tx")

        else:
            self.app.showerror("Stopped Automation","Submitting transfer cancelled upstream.")
        self.app.preview_cancel()




