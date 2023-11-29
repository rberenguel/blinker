import math
import sys
import time

from picoscroll import HEIGHT, WIDTH, PicoScroll


def interp(s, a, b):
    # Interpolating between 0 and 1 for s between output values a and b
    if s <= 0:
        return a
    if s >= 1:
        return b
    return s * b + (1 - s) * a


def lower_corners(brightness):
    return [[WIDTH - 1, 0, brightness], [WIDTH - 1, HEIGHT - 1, brightness]]


def all_pixels(brightness):
    return [[x, y, brightness] for x in range(WIDTH) for y in range(HEIGHT)]


########################################################################


class Blinker:
    DEBOUNCE = 0.2
    HIGH_BPM = 150
    LOW_BPM = 54

    def __init__(self, scroll):
        self.brightness = 40
        self._beat = True
        self._show_brightness = (
            False  # A bit of a misnomer: it is to prevent incrementing on the first tap
        )
        self._show_time = False
        self.length_mins = 25
        self._scroll = scroll
        self.oval = self.generate_oval()

    def decay_mins(self):
        return self.length_mins / 3.0

    def generate_oval(self):
        oval = []
        b_cont = (self.brightness - 20) / 80.0
        V = interp(b_cont, 7, 17)
        W = interp(b_cont, 4, 7)
        for x in range(WIDTH):
            for y in range(HEIGHT):
                v = -min(0, (x - 8) * (x - 8) / W - V)
                w = -min(0, (y - 3) * (y - 3) - W)
                bri = min(self.brightness, self.brightness * w * v / (V * W))
                if bri < 1.5:
                    bri = 0
                if bri > 1.5 and bri < 2.1:
                    bri = 2
                oval.append([x, y, int(bri)])
        return oval

    def inc_brightness(self):
        self.brightness = int(self.brightness)
        if self._show_brightness:
            self.brightness += 10
        if self.brightness > 101:
            self.brightness = 20
            self._show_brightness = False

    def inc_length(self):
        if self._show_time:
            self.length_mins += 5
        if self.length_mins > 61:
            self.length_mins = 5
            self._show_time = False

    def beat_it(self, duration, pixels=None, steps=25):
        # Pixels is x, y, max_brightness
        if pixels is None:
            pixels = self.oval
        self._scroll.clear()
        self._scroll.show()
        step_length = duration / steps
        brightness = 0

        def brightness_up():
            self._show_brightness = True
            self.inc_brightness()
            self.oval = self.generate_oval()
            time.sleep(self.DEBOUNCE)

        def stop():
            self._scroll.clear()
            self._scroll.show()
            self._beat = False
            self._show_brightness = False

        # Beat up
        for i in range(int(steps / 2)):
            for idx, p in enumerate(pixels):
                step_brightness = p[2] / steps
                brightness = i * step_brightness
                self._scroll.set_pixel(p[0], p[1], int(brightness))
            self._scroll.show()
            if self._scroll.is_pressed(self._scroll.BUTTON_B):
                brightness_up()
            if self._scroll.is_pressed(self._scroll.BUTTON_X):
                stop()
            time.sleep(step_length)
        for i in range(int(steps / 2), 0, -1):
            for idx, p in enumerate(pixels):
                step_brightness = p[2] / steps
                brightness = i * step_brightness
                self._scroll.set_pixel(p[0], p[1], int(brightness))
            self._scroll.show()
            if self._scroll.is_pressed(self._scroll.BUTTON_B):
                brightness_up()
            if self._scroll.is_pressed(self._scroll.BUTTON_X):
                stop()
            time.sleep(step_length)
        if self._scroll.is_pressed(self._scroll.BUTTON_X):
            stop()
        if self._scroll.is_pressed(self._scroll.BUTTON_B):
            brightness_up()
        self._scroll.clear()
        self._scroll.show()

    def loop(self):
        slept = 0
        start_sleep = 60.0 / self.HIGH_BPM
        sleep_time = start_sleep
        while True:
            while self._beat:
                self.beat_it(sleep_time)
                slept += sleep_time
                sleep_time = interp(
                    slept / (self.decay_mins() * 60),
                    60.0 / self.HIGH_BPM,
                    60.0 / self.LOW_BPM,
                )
                if slept > self.length_mins * 60:
                    for i in range(5):
                        self.beat_it(0.2, all_pixels(self.brightness + 10))
                    self._beat = False

            if self._scroll.is_pressed(self._scroll.BUTTON_A):
                slept = 0
                sleep_time = start_sleep
                self._beat = True
                self._show_brightness = False
                oval = self.generate_oval()
                print(
                    f"Starting for {self.length_mins} minutes with {self.brightness} brightness"
                )
            if self._scroll.is_pressed(self._scroll.BUTTON_X):
                self._scroll.clear()
                self._scroll.show()
                self._show_brightness = False
            if self._scroll.is_pressed(self._scroll.BUTTON_B):
                self.inc_brightness()
                self._scroll.clear()
                self._scroll.show_text(str(self.brightness), 10, 0)
                for px in lower_corners(self.brightness):
                    self._scroll.set_pixel(px[0], px[1], px[2])
                self._scroll.show()
                self._show_brightness = True
                time.sleep(self.DEBOUNCE)
            if self._scroll.is_pressed(self._scroll.BUTTON_Y):
                self.inc_length()
                self._scroll.clear()
                self._scroll.show_text(str(self.length_mins), 10, 0)
                self._scroll.show()
                self._show_time = True
                time.sleep(self.DEBOUNCE)


if __name__ == "__main__":
    blinker = Blinker(PicoScroll())
    blinker.loop()


