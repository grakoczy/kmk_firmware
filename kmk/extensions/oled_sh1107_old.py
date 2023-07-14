import busio
import gc

from kmk.handlers.stock import passthrough as handler_passthrough
from kmk.keys import make_key
# import adafruit_displayio_ssd1306
import adafruit_displayio_sh1107
import displayio
import terminalio
from adafruit_display_text import label 
from adafruit_display_shapes.line import Line
from kmk.extensions import Extension
from math import sin, cos


DISPLAY_OFFSET_X = 4 
DISPLAY_OFFSET_Y = 4

class OledEntryType:
    TXT = 0
    IMG = 1
    CUBE = 2


class OledData:
    def __init__(
        self,
        entries=None,
    ):
        if entries != None:
            self.data = entries

    @staticmethod
    def oled_text_entry(x=0, y=0, text="", layer=None):
        return {
            0: text,
            1: x,
            2: y,
            3: layer,
            4: OledEntryType.TXT,
        }

    @staticmethod
    def oled_image_entry(x=0, y=0, image="", layer=None):
        odb = displayio.OnDiskBitmap(image)
        return {
            0: odb,
            1: x,
            2: y,
            3: layer,
            4: OledEntryType.IMG,
        }


class Oled(Extension):
    def __init__(
        self,
        views,
        i2c,
        width=128,
        height=64,
        # flip: bool = False,
        rotation=0,
        device_address=0x3D,
        brightness=0.8,
        brightness_step=0.1,
        locks=None
    ):
        displayio.release_displays()
        # self.rotation = 180 if flip else 0
        self._rotation = rotation
        self._i2c = i2c
        self._views = views.data
        self._width = width
        self._height = height
        self._prevLayers = 0
        self._device_address = device_address
        self._brightness = brightness
        self._brightness_step = brightness_step
        self._locks = locks
        self._background_color = 0x000000
        self._color = 0xFFFFFF
        self._CAPS = "cpslck"
        self.splash = displayio.Group()

        self.angle = 0
        self.vertices = [
            (-20, -20, -20),
            (20, -20, -20),
            (20, 20, -20),
            (-20, 20, -20),
            (-20, -20, 20),
            (20, -20, 20),
            (20, 20, 20),
            (-20, 20, 20)
            ]
        
        self.edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),
            (4, 5),
            (5, 6),
            (6, 7),
            (7, 4),
            (0, 4),
            (1, 5),
            (2, 6),
            (3, 7)
        ]


        gc.collect()

        make_key(
            names=("OLED_BRI",), on_press=self._oled_bri, on_release=handler_passthrough
        )
        make_key(
            names=("OLED_BRD",), on_press=self._oled_brd, on_release=handler_passthrough
        )

    def rotate_cube(self, angle):
        for i, vertex in enumerate(self.vertices):
            x, y, z = vertex
            x_rot = x * cos(angle) - z * sin(angle)
            z_rot = x * sin(angle) + z * cos(angle)
            self.vertices[i] = (int(x_rot), int(y), int(z_rot))
    
    def draw_cube(self, group, x, y, size):
        group.pop()
        for edge in self.edges:
            start = self.vertices[edge[0]]
            end = self.vertices[edge[1]]
            line = Line(
                x + start[0] + size, y + start[1] + size,
                x+ end[0] + size, y+ end[1] + size,
                color=0xFFFFFF
            )
            group.append(line)



    def render_oled(self, layer):
        self.splash = displayio.Group()        

        for view in self._views:
            if view[3] == layer or view[3] == None:
                if view[4] == OledEntryType.TXT:
                    self.splash.append(
                        label.Label(
                            terminalio.FONT,
                            text=view[0],
                            color=0xFFFFFF,
                            x=view[1] + DISPLAY_OFFSET_X,
                            y=view[2] + DISPLAY_OFFSET_Y,
                        )
                    )
                elif view[4] == OledEntryType.IMG:
                    self.splash.append(
                        displayio.TileGrid(
                            view[0],
                            pixel_shader=view[0].pixel_shader,
                            x=view[1] + DISPLAY_OFFSET_X,
                            y=view[2] + DISPLAY_OFFSET_Y,
                        )
                    )
        self.splash.append(
            label.Label(
                terminalio.FONT,
                text="CPSLCK",
                background_color=self._background_color,
                color=self._color,
                x=0 + DISPLAY_OFFSET_X,
                y=50 + DISPLAY_OFFSET_Y,
            )
        )
        

        # if LockStatus.get_caps_lock():
        #     splash.append(
        #         label.Label(
        #             terminalio.FONT,
        #             text="CPSLK",
        #             color=0xFFFFFF,
        #             x=100 + DISPLAY_OFFSET_X,
        #             y=50 + DISPLAY_OFFSET_Y,
        #         )
        #     )
        # else:
        #     splash.append(
        #         label.Label(
        #             terminalio.FONT,
        #             text="cpslk",
        #             color=0xFFFFFF,
        #             x=100 + DISPLAY_OFFSET_X,
        #             y=50 + DISPLAY_OFFSET_Y,
        #         )
        #     )

        gc.collect()
        self._display.show(self.splash)

    def updateOLED(self, sandbox):
        self.render_oled(sandbox.active_layers[0])
        gc.collect()

    def on_runtime_enable(self, sandbox):
        return

    def on_runtime_disable(self, sandbox):
        return

    def during_bootup(self, board):
        print("Starting oled on address: %s", hex(self._device_address))        
        print("rotation: %s, width: %s, height: %s" %(self._rotation, self._width, self._height))
        displayio.release_displays()
        display_bus = displayio.I2CDisplay(self._i2c, device_address=self._device_address)
        # i2c = busio.I2C(board.SCL, board.SDA)
        # self._display = adafruit_displayio_ssd1306.SSD1306(
        self._display = adafruit_displayio_sh1107.SH1107(
            display_bus,
            width=self._width,
            height=self._height,
            rotation=self._rotation,
            display_offset=0
        )

        self.render_oled(0)
        return

    def before_matrix_scan(self, sandbox):
        if sandbox.active_layers[0] != self._prevLayers:
            self._prevLayers = sandbox.active_layers[0]
            self.updateOLED(sandbox)
        if self._locks.get_caps_lock() and self._color == 0xffffff:
            self._background_color = 0xffffff
            self._color = 0x000000
            self.updateOLED(sandbox)
        elif self._locks.get_caps_lock() == False and self._color == 0x000000:
            self._background_color = 0x000000
            self._color = 0xffffff
            self.updateOLED(sandbox)     
        return

    def after_matrix_scan(self, sandbox):
        # print("locks: ", self._locks.get_caps_lock())        
        return

    def before_hid_send(self, sandbox):
        return

    def after_hid_send(self, sandbox):
        
        # self.angle += 1
        # self.rotate_cube(self.angle)
        # self.draw_cube(self.splash, 60, 32, 30)
        return

    def on_powersave_enable(self, sandbox):
        self.splash = displayio.Group()        
        gc.collect()
        self._display.show(self.splash)
        return

    def on_powersave_disable(self, sandbox):
        self.render_oled(0)
        return

    def _oled_bri(self, *args, **kwargs):
        self._display.brightness = (
            self._display.brightness + self._brightness_step
            if self._display.brightness + self._brightness_step <= 1.0
            else 1.0
        )
        self._brightness = self._display.brightness  # Save current brightness

    def _oled_brd(self, *args, **kwargs):
        self._display.brightness = (
            self._display.brightness - self._brightness_step
            if self._display.brightness - self._brightness_step >= 0.1
            else 0.1
        )
        self._brightness = self._display.brightness  # Save current brightness