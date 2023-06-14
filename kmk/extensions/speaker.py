import board
import time
import audiocore
import audiomixer
import audiopwmio
import digitalio

from kmk.extensions import Extension


class SpeakerType(Extension):
    def __init__(self, enabled=True, pin=board.GP9):
        self.enable = enabled
        self.flag = False
        # Buzzer
        try:
            self.data = open("click-button.wav", "rb")
            self.click = audiocore.WaveFile(self.data)
            self.intro_data = open("tada.wav", "rb")
            self.intro = audiocore.WaveFile(self.intro_data)
            self.speaker = audiopwmio.PWMAudioOut(pin)
        except Exception as e:
            print(e)
            raise InvalidExtensionEnvironment(
                'Unable to create pwmio.PWMOut() instance with provided pin'
            )
        self.OFF = 0
        self.ON = 2**15
        self.SOFT = 2**12
        self.speaker.play(self.intro)
        while self.speaker.playing:
            pass

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
                    if self.speaker.playing:
                        self.speaker.stop()
                    self.speaker.play(self.click)
                    # self.buzzer.duty_cycle = self.SOFT
                    # self.buzzer.frequency = 1000
                    # time.sleep(0.05)
                    # self.buzzer.duty_cycle = self.OFF
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