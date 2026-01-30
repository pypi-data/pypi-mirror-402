import smbus2
import time

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import Adafruit_SSD1306 as SSD


class OLED(object):
    """Control of OLED display equipment."""

    def __init__(
        self, i2c_bus_number: int = 1, row_height: int = 8, debug: bool = False
    ):
        if not isinstance(i2c_bus_number, int):
            raise TypeError("i2c_bus_number must be of type int")
        if not isinstance(row_height, int):
            raise TypeError("row_height must be of type int")
        if not isinstance(debug, bool):
            raise TypeError("debug must be of type bool")

        self.__i2c_bus = i2c_bus_number
        self.__row_height = row_height
        self.__debug = debug
        # store the text content to be displayed
        self.__text = ""
        # store the point coordinates of the line chart
        self.__points = []
        # store multiple lines of text
        self.__text_0 = ""
        self.__text_1 = ""
        self.__text_2 = ""
        self.__text_3 = ""
        # 0 - init mode, 1 - text mode, 2 - text row mode, 3 - line mode
        self.__display_mode = 0
        # maximize the use of the entire OLED screen
        self.__init_y = -2
        self.__init_x = 0

        # OLED screen width and height
        self.__width = 128
        self.__height = 32
        self.__image = Image.new("1", (self.__width, self.__height))
        self.__draw = ImageDraw.Draw(self.__image)
        self.__font = ImageFont.load_default()

    def __del__(self):
        if self.__debug:
            print("OLED End!")

    def init(self):
        """Initialize OLED, return True on success, False on failure."""

        i2c_bus = self.__i2c_bus

        try:
            oled = SSD.SSD1306_128_32(rst=None, i2c_bus=i2c_bus, gpio=1)
        except Exception as e:
            raise ValueError(
                "init SSD1306_128_32 failed: {}, i2c_bus[{}]".format(e, i2c_bus)
            )
        if self.__debug:
            print("init oled done")

        try:
            oled.begin()
        except Exception as e:
            raise RuntimeError("init begin failed: {}".format(e))

        if self.__debug:
            print("oled begin")

        try:
            oled.clear()
        except Exception as e:
            raise RuntimeError("init clear failed: {}".format(e))

        if self.__debug:
            print("oled clear")

        try:
            oled.display()
        except Exception as e:
            raise RuntimeError("init display failed: {}".format(e))

        if self.__debug:
            print("oled display")

        self.__oled = oled

    def clear(self, refresh: bool = False):
        """
        Clear the display:
        refresh =True refresh immediately, refresh=False opposite.
        """

        if not isinstance(refresh, bool):
            raise TypeError("refresh must be of type bool")

        draw = self.__draw
        width = self.__width
        height = self.__height
        self.__text = ""
        self.__points = []
        self.__text_0 = ""
        self.__text_1 = ""
        self.__text_2 = ""
        self.__text_3 = ""

        # Upper left corner coordinates is (0, 0)
        # Lower right corner coordinates is (width, height)
        # Border color is 0 (black)
        # Inner fill color is 0 (black)
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        if refresh:
            try:
                self.refresh()
            except Exception as e:
                raise RuntimeError("OLED refresh failed: {}".format(e))

        if self.__debug:
            print("not refresh right now")

    def add_line(self, points: list, refresh: bool = False):
        """Draw a line chart."""
        if not isinstance(points, list):
            raise TypeError("points must be of type list")
        if not isinstance(refresh, bool):
            raise TypeError("refresh must be of type bool")

        draw = self.__draw
        width = self.__width
        height = self.__height

        self.__points = points
        self.__display_mode = 3

        min_v = 0
        max_v = 0
        # [(0, 1), (1, 5), (2, 9)...]
        for i, p in points:
            if i == 0:
                min_v = p
                max_v = p
            else:
                if p > max_v:
                    max_v = p
                else:
                    min_v = p

        if len(points) > width:
            raise ValueError(
                "input out of display range, max point length is {}, but input length is {}".format(
                    width, len(points)
                )
            )
        elif min_v < 0 or max_v > height:
            raise ValueError(
                "input out of display range, max point value is {}, min point value is {}, it should be in range [0, {}]".format(
                    max_v, min_v, height
                )
            )
        else:
            draw.line(points, fill=255)
            if self.__debug:
                print("draw text now")
            if refresh:
                self.refresh()

    def get_line(self) -> list:
        """Get the current line chart points."""
        return self.__points

    def add_text(self, start_x: int, start_y: int, text: str, refresh: bool = False):
        """
        Add characters:
        start_x and start_y indicates the starting point, text is the character to be added,
        refresh =True refresh immediately, refresh=False opposite.
        """

        if not isinstance(start_x, int):
            raise TypeError("start_x must be of type int")
        if not isinstance(start_y, int):
            raise TypeError("start_y must be of type int")
        if not isinstance(text, str):
            raise TypeError("text must be of type str")
        if not isinstance(refresh, bool):
            raise TypeError("refresh must be of type bool")

        draw = self.__draw
        width = self.__width
        height = self.__height
        font = self.__font

        self.__text = text
        self.__display_mode = 1

        if start_x > width or start_x < 0 or start_y < 0 or start_y > height:
            raise ValueError("input out of display range")
        else:
            init_x = self.__init_x
            init_y = self.__init_y
            x = start_x + init_x
            y = start_y + init_y
            # The upper left corner of the text is (x, y) with white text (fill=255)
            draw.text((x, y), text, font=font, fill=255)
            if self.__debug:
                print("draw text now")
            if refresh:
                self.refresh()

    def get_text(self) -> str:
        """Get the current text content."""
        return self.__text

    def add_row(self, text: str, row: int = 0, refresh: bool = False):
        """
        Write a line of character text:
        refresh =True, refresh immediately, refresh=False opposite,
        line=0, 1, 2, 3, total 4 rows.
        """

        if not isinstance(text, str):
            raise TypeError("text must be of type str")
        if not isinstance(row, int):
            raise TypeError("row must be of type int")
        if not isinstance(refresh, bool):
            raise TypeError("refresh must be of type bool")

        if row == 0:
            self.__text_0 = text
        elif row == 1:
            self.__text_1 = text
        elif row == 2:
            self.__text_2 = text
        elif row == 3:
            self.__text_3 = text

        self.__display_mode = 2

        if row < 0 or row > 3:
            raise ValueError("oled line input error")
        else:
            row_height = self.__row_height
            y = row_height * row
            self.add_text(0, y, text, refresh)
            if self.__debug:
                print("add row now")

    def get_rows(self, row: int) -> str:
        """Get the lines of text content."""
        if not isinstance(row, int):
            raise TypeError("row must be of type int")

        if row == 0:
            return self.__text_0
        elif row == 1:
            return self.__text_1
        elif row == 2:
            return self.__text_2
        elif row == 3:
            return self.__text_3
        else:
            raise ValueError("row must be between 0 and 3")

    def refresh(self):
        """Refresh the OLED to display the content"""
        oled = self.__oled
        image = self.__image
        oled.image(image)
        oled.display()

    def get_display_mode(self) -> str:
        """Get the current display mode."""
        if self.__display_mode == 0:
            return "init"
        elif self.__display_mode == 1:
            return "text"
        elif self.__display_mode == 2:
            return "text_row"
        elif self.__display_mode == 3:
            return "line"


class Cube(object):
    """Control of peripheral devices such as fans and lights."""

    def __init__(
        self, i2c_bus_number: int = 1, delay: float = 0.002, debug: bool = False
    ):
        if not isinstance(i2c_bus_number, int):
            raise TypeError("i2c_bus_number must be of type int")
        if not isinstance(delay, float):
            raise TypeError("delay must be of type float")
        if not isinstance(debug, bool):
            raise TypeError("debug must be of type bool")

        self.__delay = delay
        self.__debug = debug

        self.__i2c_bus = smbus2.SMBus(i2c_bus_number)

        # config settting
        self.__i2c_addr = 0x0E
        self.__reg_version = 0x00
        self.__reg_rgb_effect = 0x04
        self.__reg_rgb_speed = 0x05
        self.__reg_rgb_color = 0x06
        self.__reg_rgb_off = 0x07
        self.__reg_fan = 0x08

    def __del__(self):
        if self.__debug:
            print("Cube End!")

    def set_fan(self, state: int):
        """
        Control fan:
        start=0 close, start=1 open.
        """

        if not isinstance(state, int):
            raise TypeError("state must be of type int")

        if state > 0:
            state = 1
        else:
            state = 0

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_fan = self.__reg_fan
        delay = self.__delay

        try:
            conn.write_byte_data(i2c_addr, reg_fan, state)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            raise RuntimeError("set_fan failed: {}".format(e))

        if self.__debug:
            print("set_fan ok")

    def get_fan(self) -> int:
        """Obtain the current fan status: 0 off, 1 on."""

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_fan = self.__reg_fan

        try:
            state = conn.read_byte_data(i2c_addr, reg_fan)
        except Exception as e:
            raise RuntimeError("get_fan failed: {}".format(e))

        return state

    def set_rgb_effect(self, effect: int):
        """
        Control RGB light effect:
        0 off effect, 1 breathing light, 2 marquee light, 3 rainbow light,
        4 dazzling lights, 5 running water lights, 6 circulation breathing lights.
        """

        if not isinstance(effect, int):
            raise TypeError("effect must be of type int")

        if effect < 0:
            effect = 0
        elif effect > 6:
            effect = 6

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_effect = self.__reg_rgb_effect
        delay = self.__delay

        try:
            conn.write_byte_data(i2c_addr, reg_rgb_effect, effect)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            raise RuntimeError("set_rgb_effect failed: {}".format(e))

        if self.__debug:
            print("set_rgb_effect ok")

    def set_rgb(self, state: int):
        """
        Control RGB light:
        state=0 off, state=1 on.
        """

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_off = self.__reg_rgb_off
        delay = self.__delay

        try:
            conn.write_byte_data(i2c_addr, reg_rgb_off, state)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            raise RuntimeError("set_rgb failed: {}".format(e))
        if self.__debug:
            print("set_rgb ok")

    def get_rgb(self) -> int:
        """Obtain the current RGB light status: 0 off, 1 on."""

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_off = self.__reg_rgb_off

        try:
            state = conn.read_byte_data(i2c_addr, reg_rgb_off)
        except Exception as e:
            raise RuntimeError("get_rgb failed: {}".format(e))

        return state

    def get_rgb_effect(self) -> int:
        """Obtain the current RGB light effect."""

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_effect = self.__reg_rgb_effect

        try:
            effect = conn.read_byte_data(i2c_addr, reg_rgb_effect)
        except Exception as e:
            raise RuntimeError("get_rgb_effect failed: {}".format(e))

        return effect

    def set_rgb_speed(self, speed: int):
        """
        Set RGB light effect speed:
        1 low speed, 2 medium speed, 3 high speed.
        """

        if not isinstance(speed, int):
            raise TypeError("speed must be of type int")

        if speed < 1:
            speed = 1
        elif speed > 3:
            speed = 3

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_speed = self.__reg_rgb_speed
        delay = self.__delay

        try:
            conn.write_byte_data(i2c_addr, reg_rgb_speed, speed)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            raise RuntimeError("set_rgb_speed failed: {}".format(e))

        if self.__debug:
            print("set_rgb_speed ok")

    def get_rgb_speed(self) -> int:
        """Obtain the current RGB light effect speed."""

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_speed = self.__reg_rgb_speed

        try:
            speed = conn.read_byte_data(i2c_addr, reg_rgb_speed)
        except Exception as e:
            raise RuntimeError("get_rgb_speed failed: {}".format(e))

        return speed

    def set_rgb_color(self, color: int):
        """
        Set RGB light effect color:
        0 red, 1 green, 2 blue, 3 yellow, 4 purple, 5 cyan, 6 white.
        """

        if not isinstance(color, int):
            raise TypeError("color must be of type int")

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_color = self.__reg_rgb_color
        delay = self.__delay

        if color < 0:
            color = 0
        elif color > 6:
            color = 6

        try:
            conn.write_byte_data(i2c_addr, reg_rgb_color, color)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            raise RuntimeError("set_rgb_color failed: {}".format(e))

        if self.__debug:
            print("set_rgb_color ok")

    def get_rgb_color(self) -> int:
        """Obtain the current RGB light effect color."""

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_color = self.__reg_rgb_color

        try:
            color = conn.read_byte_data(i2c_addr, reg_rgb_color)
        except Exception as e:
            raise RuntimeError("get_rgb_color failed: {}".format(e))

        return color

    def set_single_color(self, index: int, r: int, g: int, b: int):
        """
        Set the individual RGB light color:
        index indicates the serial number of the lamp bead 0-13, index=255 means to control all lamps,
        r stands for red, g stands for green, and b stands for blue.
        """

        if not isinstance(index, int):
            raise TypeError("index must be of type int")
        if not isinstance(r, int):
            raise TypeError("r must be of type int")
        if not isinstance(g, int):
            raise TypeError("g must be of type int")
        if not isinstance(b, int):
            raise TypeError("b must be of type int")

        self.__rgb_index = index
        self.__rgb_r = r
        self.__rgb_g = g
        self.__rgb_b = b

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_effect = self.__reg_rgb_effect
        delay = self.__delay

        try:
            # Turn off RGB light effects
            conn.write_byte_data(i2c_addr, reg_rgb_effect, 0)
            conn.write_byte_data(i2c_addr, 0x00, index & 0xFF)
            conn.write_byte_data(i2c_addr, 0x01, r & 0xFF)
            conn.write_byte_data(i2c_addr, 0x02, g & 0xFF)
            conn.write_byte_data(i2c_addr, 0x03, b & 0xFF)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            raise RuntimeError("set_single_color failed: {}".format(e))

        if self.__debug:
            print("set_single_color ok")

    def get_version(self) -> int:
        """Obtain the firmware version number."""

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        version = self.__reg_version

        try:
            version = conn.read_byte_data(i2c_addr, version)
        except Exception as e:
            raise RuntimeError("get_version failed: {}".format(e))
        else:
            return version
