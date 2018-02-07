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

if False: # TODO detect if raspi
    from picamera import PiCamera
    class Scanner(object):
        def __init__(self,verbose=False):
            self.verbose = verbose
            self.camera = None

        def start(self,):
            self.camera = PiCamera()
            time.sleep(1)
            self.camera.start_preview(fullscreen=False, window = (100, 20, 640, 480)) # alpha = 255 rotation=0, vflip=False, hflip=False
            # https://picamera.readthedocs.io/en/release-1.10/api_renderers.html?highlight=renderer#picamera.renderers.PiPreviewRenderer

        def stop(self,):
            if self.camera is not None:
                #self.camera.stop_preview()
                self.camera.close()
            self.camera = None

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
            image = Image.open(stream)

            codes = zbarlight.scan_codes('qrcode', image)
            codes = [b(i) for i in codes]
            if verbose:
                for i in codes:
                    print('QR code: %s' % i)

            return codes

class Payload(object):
    def __init__(self,msgType,verbose=False):
        self.verbose = verbose
        self.msgType = msgType
        self.pattern = re.compile(self.msgType + r",(?P<crc>[a-z0-9]{8}),(?P<rank>[0-9]{1,3})/(?P<total>[0-9]{1,3}):(?P<payload>\S+)")
        self.bin = []

    def _use(self,match):
        index = int(match.group("rank")) - 1
        self.bin[index] = match.group("payload")
        if self.verbose: print("found:",index)

    def digest(self,codes):
        if not self.bin:
            for code in codes:
                match = self.pattern.fullmatch(code)
                if match:
                    self.bin = [0 for i in range(int(match.group("total")))]
                    self.crc = match.group("crc")
                    self._use(match)
                    self.pattern = re.compile(self.msgType + "," + self.crc + r",(?P<rank>[0-9]{1,3})/%s:(?P<payload>\S+)"% match.group("total"))
                    break
            self.digest(codes)
        else:
            for code in codes:
                match = self.pattern.fullmatch(code)
                if match:
                    self._use(match)

    def stitched(self):
        if self.__bool__():
            return "".join(i for i in self.bin).strip()
        else:
            raise Exception("Payload Error: Payload was not ready to be stitched\n%s" % self.bin)

    def prepared(self):
        finished = base64.b64decode(self.stitched())
        prev = 0
        prev = zlib.crc32(finished, prev)
        actual_crc = "%x"%(prev & 0xFFFFFFFF)
        return finished, bool(self.crc == actual_crc)






    def toFile(self,path):
        pass
    def __bool__(self):
        if self.bin:
            if not 0 in self.bin:
                return True
        return False

    def __nonzero__(self):
        return self.__bool__()

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



