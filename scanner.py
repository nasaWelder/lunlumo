# camera functions
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


# picamera capture to PIL Image

from io import BytesIO
import time
from picamera import PiCamera
from PIL import Image
import zbarlight



class Scanner(object):
    def __init__(self,vebose=False):
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
        if verbose:
            print('QR codes: %s' % codes[0].decode("utf-8"))

        return codes

