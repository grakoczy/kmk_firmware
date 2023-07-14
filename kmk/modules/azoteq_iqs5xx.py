'''
Extension handles usage AZOTEQ touchpad, tested on TPS65-201A-S
Based on work of Frank Adams
https://github.com/thedalles77/USB_Laptop_Keyboard_Controller/blob/master/Example_Touchpads/Azoteq_TP.ino
'''

from micropython import const

import math
import struct
import time
import digitalio

from kmk.keys import AX, KC, make_argumented_key, make_key
from kmk.kmktime import PeriodicTimer
from kmk.modules import Module
from kmk.utils import Debug




class Touchpad(Module):
    '''Module handles usage of AZOTEQ touchpad'''

    def __init__(
        self,
        i2c,
        rdy_pin = 0,
        reset_pin = 0,
        click = True,
        click_max_y = 100,
    ):
        self.I2C_ADDRESS = const(0x74)

        self.GESTURE0 = 0 # holds gesture events 0
        self.GESTURE1 = 0 # holds gesture events 1
        self.SYS_INFO0 = 0 # holds system info 0
        self.SYS_INFO1 = 0 # holds system info 1
        self.FINGER_COUNT = 0 # number of fingers
        self.XREL_HIGH = 0 # holds the relative x high 8 bits
        self.XREL_LOW = 0 # holds the relative x low 8 bits
        self.YREL_HIGH = 0 # holds the relative y high 8 bits
        self.YREL_LOW = 0 # holds the relative y low 8 bits
        self.XABS_HIGH = 0 # holds the absolute x high 8 bits
        self.XABS_LOW = 0 # holds the absolute x low 8 bits
        self.YABS_HIGH = 0 # holds the absolute y high 8 bits
        self.YABS_LOW = 0 # holds the absolute y low 8 bits
        self.TCH_STRENGTH_HIGH = 0 # holds the touch strength high 8 bits
        self.TCH_STRENGTH_LOW = 0 # holds the touch strength low 8 bits
        self.TCH_AREA = 0 # holds the touch area/size
        self.LEFT_BUTTON = 0 # Active high, on/off variable for left button 
        self.OLD_LEFT_BUTTON = 0 # Active high, on/off variable for left button status from the previous polling cycle
        self.LEFT_BUTTON_CHANGE = 0 # Active high, shows when a touchpad left button has changed since the last polling cycle
        self.RIGHT_BUTTON = 0 # Active high, on/off variable for right button 
        self.OLD_RIGHT_BUTTON = 0 # Active high, on/off variable for right button status from the previous polling cycle
        self.RIGHT_BUTTON_CHANGE = 0 # Active high, shows when a touchpad right button has changed since the last polling cycle

        # self._i2c_address = address
        self._i2c_bus = i2c
        self._rdy = digitalio.DigitalInOut(rdy_pin) # touchpad ready signal monitored by board, active high
        self._rst_n = digitalio.DigitalInOut(reset_pin) # touchpad reset, active low
        self._rdy.direction = digitalio.Direction.INPUT
        self._rst_n.direction = digitalio.Direction.OUTPUT        
        self._click = click
        self._click_max_y = click_max_y
        self.polling_interval = 20

        self.register = bytearray([0x00, 0x0d])
        self.end_sequence = bytearray([0xee, 0xee, 0x00])
        self.result = bytearray(44)


    def during_bootup(self, keyboard):
        print("Starting touchpad")
        
        self._rst_n.value = False
        time.sleep(0.2)
        self._rst_n.value = True

        self._timer = PeriodicTimer(self.polling_interval)
        

    def before_matrix_scan(self, keyboard):
        '''
        Return value will be injected as an extra matrix update
        '''
        if not self._timer.tick():
            return

        if self._rdy.value:
            if not self._i2c_bus.try_lock():
                return

            try:
                # select register
                self._i2c_bus.writeto(self.I2C_ADDRESS, self.register)
                self._i2c_bus.readfrom_into(self.I2C_ADDRESS, self.result)

                # Send the End Communication Window Command per para 8.7 of Azoteq data sheet
                self._i2c_bus.writeto(self.I2C_ADDRESS, self.end_sequence); 
                self.GESTURE0 = self.result[0] # read the gesture 0 byte from register 0x000d
                self.GESTURE1 = self.result[1] # read the gesture 1 byte from register 0x000e
                self.SYS_INFO0 = self.result[2] # read the system info 0 byte from register 0x000f
                self.SYS_INFO1 = self.result[3] # read the system info 1 byte from register 0x0010
                self.FINGER_COUNT = self.result[4] # read the finger count byte from register 0x0011
                self.XREL_HIGH = self.result[5] # read the high relative X byte from register 0x0012
                self.XREL_LOW = self.result[6] # read the low relative X byte from register 0x0013
                self.YREL_HIGH = self.result[7] # read the high relative Y byte from register 0x0014
                self.YREL_LOW = self.result[8] # read the low relative Y byte from register 0x0015
                self.XABS_HIGH = self.result[9] # read the high absolute X byte from register 0x0016
                self.XABS_LOW = self.result[10] # read the low absolute X byte from register 0x0017
                self.YABS_HIGH = self.result[11] # read the high absolute Y byte from register 0x0018
                self.YABS_LOW = self.result[12] # read the low absolute Y byte from register 0x0019
                self.TCH_STRENGTH_HIGH = self.result[13] # read the high touch strength byte from register 0x001a
                self.TCH_STRENGTH_LOW = self.result[14] # read the low touch strength byte from register 0x001b
                self.TCH_AREA = self.result[15] # read the touch area/size byte from register 0x001c
            finally:
                self._i2c_bus.unlock()

            x = 0
            y = 0
            abs_y = (self.YABS_HIGH << 8) | self.YABS_LOW
            
            if ((self.XREL_LOW != 0x00) or (self.YREL_LOW != 0x00)):            
                if(self.XREL_HIGH != 255):
                    x = self.XREL_LOW
                else:
                    x = (255-self.XREL_LOW)*-1
                if(self.YREL_HIGH != 255):
                    y = self.YREL_LOW
                else:
                    y = (255-self.YREL_LOW)*-1            

            if self.FINGER_COUNT == 1:
                AX.X.move(keyboard, x)
                AX.Y.move(keyboard, y)
            if self.FINGER_COUNT == 2:
                AX.W.move(keyboard, -int(y/8))

            if ((self.GESTURE0 & 0x01) == 0x01) and (768-abs_y)<self._click_max_y : # test bit 0
                self.LEFT_BUTTON = True
            else:
                self.LEFT_BUTTON = False      

            # Determine if the left touchpad button has changed since last polling cycle using xor
            self.LEFT_BUTTON_CHANGE = self.LEFT_BUTTON ^ self.OLD_LEFT_BUTTON
            # Don't send button status if there's no change since last time. 
            self.OLD_LEFT_BUTTON = self.LEFT_BUTTON; # remember button status for next polling cycle
            if self.LEFT_BUTTON_CHANGE and self._click:
                keyboard.pre_process_key(KC.MB_LMB, is_pressed=self.LEFT_BUTTON)

            if ((self.GESTURE1 & 0x01) == 0x01): # test bit 0
                self.RIGHT_BUTTON = True
            else:
                self.RIGHT_BUTTON = False

            # Determine if the left touchpad button has changed since last polling cycle using xor
            self.RIGHT_BUTTON_CHANGE = self.RIGHT_BUTTON ^ self.OLD_RIGHT_BUTTON
            # Don't send button status if there's no change since last time. 
            if self.RIGHT_BUTTON_CHANGE and self._click:
                keyboard.pre_process_key(KC.MB_RMB, is_pressed=self.RIGHT_BUTTON)        
            self.OLD_RIGHT_BUTTON = self.RIGHT_BUTTON; # remember button status for next polling cycle


    def after_matrix_scan(self, keyboard):
        return

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        if self._click:
            if self.LEFT_BUTTON:
                keyboard.pre_process_key(KC.MB_LMB, is_pressed=False)
            if self.RIGHT_BUTTON:
                keyboard.pre_process_key(KC.MB_RMB, is_pressed=False)   
        return

    def on_powersave_enable(self, keyboard):
        return

    def on_powersave_disable(self, keyboard):
        return

        


