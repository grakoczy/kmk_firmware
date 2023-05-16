import board
import pwmio
import time

from kmk.extensions import Extension


class BuzzerType(Extension):
    def __init__(self, enabled=True):
        self.enable = enabled
        self.flag = False
        # Buzzer
        try:
            self.buzzer = pwmio.PWMOut(board.GP9, variable_frequency=True)
        except Exception as e:
            print(e)
            raise InvalidExtensionEnvironment(
                'Unable to create pwmio.PWMOut() instance with provided pin'
            )
        self.OFF = 0
        self.ON = 2**15
        self.SOFT = 2**12
        self.buzzer.duty_cycle = self.ON
        self.buzzer.frequency = 2000
        time.sleep(0.1)
        self.buzzer.frequency = 1000
        time.sleep(0.1)
        self.buzzer.duty_cycle = self.OFF

    def on_runtime_enable(self, keyboard):
        return

    def on_runtime_disable(self, keyboard):
        return

    def during_bootup(self, keyboard):
        return

    def before_matrix_scan(self, keyboard):
        return

    def after_matrix_scan(self, keyboard):
        if self.enable:
            if keyboard.matrix_update or keyboard.secondary_matrix_update:
                self.flag = not self.flag
                if self.flag:
                    self.buzzer.duty_cycle = self.SOFT
                    self.buzzer.frequency = 1000
                    time.sleep(0.05)
                    self.buzzer.duty_cycle = self.OFF
        return

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return

    def on_powersave_enable(self, keyboard):
        self.enable = False
        return

    def on_powersave_disable(self, keyboard):
        self.enable = True
        return