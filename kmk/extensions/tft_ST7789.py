import busio
import gc

from kmk.handlers.stock import passthrough as handler_passthrough
from kmk.keys import make_key
from adafruit_st7789 import ST7789
import displayio
import terminalio
from adafruit_display_text import label
from kmk.extensions import Extension


DISPLAY_OFFSET_X = 2  
DISPLAY_OFFSET_Y = 2

class tftEntryType:
    TXT = 0
    IMG = 1


class TFTData:
    def __init__(
        self,
        entries=None,
    ):
        if entries != None:
            self.data = entries

    @staticmethod
    def tft_text_entry(x=0, y=0, text="", layer=None):
        return {
            0: text,
            1: x,
            2: y,
            3: layer,
            4: tftEntryType.TXT,
        }

    @staticmethod
    def tft_image_entry(x=0, y=0, image="", layer=None):
        odb = displayio.OnDiskBitmap(image)
        return {
            0: odb,
            1: x,
            2: y,
            3: layer,
            4: tftEntryType.IMG,
        }


class TFT(Extension):
    def __init__(
        self,
        views,
        spi=None,
        width=280,
        height=240,
        tft_cs=0,
        tft_dc=0,
        reset=0,
        # flip: bool = False,
        rotation=0,
        locks=None
    ):
        displayio.release_displays()
        # self.rotation = 180 if flip else 0
        self._rotation = rotation
        self._views = views.data
        self._spi = spi
        self._tft_cs = tft_cs
        self._tft_dc = tft_dc
        self._reset = reset
        self._width = width
        self._height = height
        self._prevLayers = 0
        self._locks = locks
        self._background_color = 0x000000
        self._color = 0xFFFFFF
        self._CAPS = "cpslck"
        gc.collect()


    def render_tft(self, layer):
        splash = displayio.Group()
        self._display.show(splash)       

        for view in self._views:
            if view[3] == layer or view[3] == None:
                if view[4] == tftEntryType.TXT:
                    splash.append(
                        label.Label(
                            terminalio.FONT,
                            scale=2,
                            text=view[0],
                            color=0xFFFFFF,
                            x=view[1] + DISPLAY_OFFSET_X,
                            y=view[2] + DISPLAY_OFFSET_Y,
                        )
                    )
                elif view[4] == tftEntryType.IMG:
                    splash.append(
                        displayio.TileGrid(
                            view[0],
                            pixel_shader=view[0].pixel_shader,
                            x=view[1] + DISPLAY_OFFSET_X,
                            y=view[2] + DISPLAY_OFFSET_Y,
                        )
                    )
        splash.append(
            label.Label(
                terminalio.FONT,
                text="CPSLCK",
                background_color=self._background_color,
                color=self._color,
                x=0 + DISPLAY_OFFSET_X,
                y=50 + DISPLAY_OFFSET_Y,
            )
        )

        

        gc.collect()
        

    def updatetft(self, sandbox):
        self.render_tft(sandbox.active_layers[0])
        gc.collect()

    def on_runtime_enable(self, sandbox):
        return

    def on_runtime_disable(self, sandbox):
        return

    def during_bootup(self, board):
        print("rotation: %s, width: %s, height: %s" %(self._rotation, self._width, self._height))
        displayio.release_displays()
        # print("spi: ", self._spi)
        # while not self._spi.try_lock():
        #     print("waiting for spi")
        # self._spi.configure(baudrate=48000000) # Configure SPI for 24MHz
        # self._spi.unlock()
        print("starting display")
        display_bus = displayio.FourWire(self._spi, command=self._tft_dc, chip_select=self._tft_cs, reset=self._reset)
        self._display = ST7789(display_bus, width=self._width, height=self._height, rowstart=20, rotation=self._rotation)
        # print("display started")
        
        self.render_tft(0)
        return

    def before_matrix_scan(self, sandbox):
        if sandbox.active_layers[0] != self._prevLayers:
            self._prevLayers = sandbox.active_layers[0]
            self.updatetft(sandbox)
        if self._locks.get_caps_lock() and self._color == 0xffffff:
            self._background_color = 0xffffff
            self._color = 0x000000
            self.updatetft(sandbox)
        elif self._locks.get_caps_lock() == False and self._color == 0x000000:
            self._background_color = 0x000000
            self._color = 0xffffff
            self.updatetft(sandbox)     
        return

    def after_matrix_scan(self, sandbox):
        # print("locks: ", self._locks.get_caps_lock())        
        return

    def before_hid_send(self, sandbox):
        return

    def after_hid_send(self, sandbox):
        return

    