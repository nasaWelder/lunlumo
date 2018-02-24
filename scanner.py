# scanner.py camera functions
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
from io import BytesIO
import time

from PIL import Image
import zbarlight
import re
import sys
import base64
import zlib
if sys.version_info < (3,):
    def b(x):
        return x
else:
    def b(x):
        return x.decode("utf-8")

try:
    from picamera import PiCamera
except Exception as e:
    print("\n\nUnable to import picamera!!\n\n")
    print(str(e))
else:
    class Scanner_picamera(object):
        def __init__(self,verbose=False):
            self.verbose = verbose
            self.camera = None
            self.still = None

        def start(self,):
            if self.camera is None:
                self.camera = PiCamera()
                time.sleep(1)
                #no preview because we can handle it in tkinter
                #self.camera.start_preview(fullscreen=False, window = (100, 20, 640, 480)) # alpha = 255 rotation=0, vflip=False, hflip=False
                # https://picamera.readthedocs.io/en/release-1.10/api_renderers.html?highlight=renderer#picamera.renderers.PiPreviewRenderer

        def stop(self,):
            if not self.camera is None:
                #self.camera.stop_preview()
                self.camera.close()
            self.camera = None

        def snapshot(self,snapshot_size = (256,256)):
            if self.still:
                thumb = self.still.copy()
                thumb.thumbnail(snapshot_size,Image.ANTIALIAS)
                #time.sleep(.25)
                return thumb
            else:
                return None

        def scan(self,verbose=False):
            #### picamera capture to PIL Image

            # Create the in-memory stream
            stream = BytesIO()

            self.camera.capture(stream, format='jpeg',use_video_port= False)   # perhaps change from jpeg to gif or png
            ###
            ''' The use_video_port parameter controls whether the camera’s image or video port is used to capture images.
            It defaults to False which means that the camera’s image port is used. This port is slow but produces better
             quality pictures. If you need rapid capture up to the rate of video frames, set this to True.'''
            ###

            # "Rewind" the stream to the beginning so we can read its content
            stream.seek(0)
            self.still = Image.open(stream)

            codes = zbarlight.scan_codes('qrcode', self.still)
            codes = [b(i) for i in codes]
            if verbose:
                for i in codes:
                    print('QR code: %s' % i)

            return codes

try:
    import pygame
    import pygame.camera
    from pygame.locals import *
except Exception as e:
    print("\n\nUnable to import pygame (for v4l webcam support)!!\n\n")
    print(str(e))
else:
    class Scanner_pygame(object):
        def __init__(self,app = None,verbose=False,delay_ms = 400,resolution = (640,480)):   #(640,480)
            self.resolution = resolution
            self.app = app
            self.delay_ms = delay_ms
            pygame.init()
            pygame.camera.init()
            time.sleep(1)
            self.still = None
            self.verbose = verbose
            self.clist = pygame.camera.list_cameras()
            print("Cameras Found: %s" % self.clist)
            if not self.clist:
                raise ValueError("Sorry, no cameras detected.")
            self.camera = None
            self.children = []

        def start(self,):
            if self.camera is None:
                self.camera = pygame.camera.Camera(self.clist[0], self.resolution)
                self.camera.start()
                time.sleep(1)


        def stop(self,):
            if not self.camera is None:
                self.camera.stop()
            self.camera = None

        def snapshot(self,snapshot_size = (256,256)):
            if self.still:
                #print("found still")
                thumb = self.still.copy()
                thumb.thumbnail(snapshot_size,Image.ANTIALIAS)
                #time.sleep(.25)
                return thumb
            else:
                return None



        def scan(self,verbose=False):
            snap = self.camera.get_image()
            pil_string_image = pygame.image.tostring(snap,"RGBA",False)
            self.still = Image.frombytes("RGBA",self.resolution,pil_string_image)
            self.codes = zbarlight.scan_codes('qrcode', self.still)
            if self.codes:
                self.codes = [b(i) for i in self.codes]
                """
                if self.verbose:
                    for i in self.codes:
                        print('QR code: %s\n\n' % i)
                """
                return self.codes
            else:
                self.codes=[]
                #print("\n======\n\nNo QR Found\n\n======")
                return None

        def refresh(self,verbose=False):
            snap = self.camera.get_image()
            pil_string_image = pygame.image.tostring(snap,"RGBA",False)
            self.still = Image.frombytes("RGBA",self.resolution,pil_string_image)

        def add_child(self,child):
            #print("adding child")
            self.start()
            self.children.append(child)
            self.feed_children()

        def feed_children(self):
            if self.children:
                #print("scan()")
                self.scan()
                for child in self.children:
                    child.digest(self.codes)
                self.app._root().after(self.delay_ms,self.feed_children)
            else:
                self.stop()




class Payload(object):
    def __init__(self,msgType,scanner = None,app = None,signal_app = False,verbose=False):
        self.verbose = verbose
        self.msgType = msgType
        self.app = app
        self.signal_app = signal_app
        self.pattern = re.compile(self.msgType + r",(?P<crc>[a-z0-9]{8}),(?P<rank>[0-9]{1,3})/(?P<total>[0-9]{1,3}):(?P<payload>\S+)")
        self.bin = []

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
        if not self.bin:
            for code in codes:
                match = self.pattern.fullmatch(code)
                if match:
                    if self.app and self.signal_app:
                        self.app.payload_started()
                    self.bin = [0 for i in range(int(match.group("total")))]
                    self.crc = match.group("crc")
                    self._use(match)
                    self.pattern = re.compile(self.msgType + "," + self.crc + r",(?P<rank>[0-9]{1,3})/%s:(?P<payload>\S+)"% match.group("total"))
                    break

        else:
            for code in codes:
                match = self.pattern.fullmatch(code)
                if match:
                    self._use(match)

    def stitched(self):
        if self.got_all():
            return "".join(i for i in self.bin).strip()
        else:
            raise Exception("Payload Error: Payload was not ready to be stitched\n%r" % self.bin)

    def prepared(self):
        finished = base64.b64decode(self.stitched())
        prev = 0
        prev = zlib.crc32(finished, prev)
        text_crc = "%x"%(prev & 0xFFFFFFFF)
        return finished, bool(self.crc == text_crc)

    def toFile(self,path):
        data, success = self.prepared()
        with open(path, 'wb') as dest:
            dest.write(data)
        prev = 0
        for eachLine in open(path,"rb"):
            prev = zlib.crc32(eachLine, prev)
        actual_crc = "%x"%(prev & 0xFFFFFFFF)
        return bool(self.crc == actual_crc)

    def got_all(self):
        if self.bin:
            if not 0 in self.bin:
                return True
        return False

    def reset(self):
        self.pattern = re.compile(self.msgType + r",(?P<crc>[a-z0-9]{8}),(?P<rank>[0-9]{1,3})/(?P<total>[0-9]{1,3}):(?P<payload>\S+)")
        self.bin = []

if __name__ == "__main__":
    from PIL import ImageTk
    def get_preview():
        thumb = cam.snapshot()
        if thumb:
            preview.img = ImageTk.PhotoImage(thumb)
            preview.config(image = preview.img)
        root.after(450,get_preview)

    def get_scan():
        codes = cam.scan()
        if codes:
            status.config(text = "found:  " + codes[0].split(":")[0])
        else:
            status.config(text = "<nothing found>")
        root.attributes('-topmost', 1)
        root.after(400,get_scan)

    cam = Scanner_pygame(verbose = True)
    cam.start()
    import tkinter as tk
    root = tk.Tk()
    root.title("pygame QR code Scanner")
    frame = tk.Frame(root)
    frame.pack()
    preview = tk.Label(frame)
    preview.pack()
    status = tk.Label(frame,text = "waiting for codes")
    status.pack()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry("256x%d+%d+%d" % (int(256*480/640+20),int(0),int(h-256*480/640+20)))

    get_scan()
    get_preview()

    root.mainloop()
    cam.stop()

"""
if __name__ == "__main__":
    import timeit
    import glob
    incoming = Payload("raw",verbose = True)

    tic=timeit.default_timer()
    for f in glob.glob("signed_monero_tx.QRbatch/*.eps"):
        with open(f, 'rb') as image_file:
            image = Image.open(image_file)
            image.load()
        codes = zbarlight.scan_codes('qrcode', image)
        codes = [b(i) for i in codes]
        incoming.digest(codes)
    toc=timeit.default_timer()

    print("\ntime:",toc - tic)
    finished,success = incoming.prepared()
    print(finished)
    print(success)
"""



