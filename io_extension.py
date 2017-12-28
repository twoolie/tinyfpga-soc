#!/usr/bin/env python3

# use minispartan6 as io extension for tinyfpgab

# io         |   minispartan6   |   tinyfpgab
# serial tx  |    porta0 (E7)   |    pin5 (A2)
# serial rx  |    porta2 (D8)   |    pin5 (A1)
# led0       |    porta4 (D9)   |    pin6 (B1)
# gnd        |                  |
# led1       |    porta6  (B10) |    pin7 (C1)
# led2       |    porta8  (E10) |    pin8 (D1)
# led3       |    porta10 (F10) |    pin9 (E1)

from litex.gen import *
from litex.build.xilinx import XC3SProg
from litex.build.generic_platform import *
from litex.boards.platforms import minispartan6

_extension_io = [
    ("io_serial", 0,
        Subsignal("tx", Pins("E7")),
        Subsignal("rx", Pins("D8")),
        IOStandard("LVCMOS33")
    ),
    ("io_leds", 0, Pins("D9"), IOStandard("LVCMOS33")),
    ("io_leds", 1, Pins("B10"), IOStandard("LVCMOS33")),
    ("io_leds", 2, Pins("E10"), IOStandard("LVCMOS33")),
    ("io_leds", 3, Pins("F10"), IOStandard("LVCMOS33")),
]

plat = minispartan6.Platform(device="xc6slx25")
plat.add_extension(_extension_io)
module = Module()
counter = Signal(32)
module.sync += counter.eq(counter + 1)
serial_pads = plat.request("serial")
io_serial_pads = plat.request("io_serial")
module.comb += [
    serial_pads.tx.eq(io_serial_pads.rx),
    io_serial_pads.rx.eq(serial_pads.rx),
    plat.request("user_led", 0).eq(plat.request("io_leds", 0)),
    plat.request("user_led", 1).eq(plat.request("io_leds", 1)),
    plat.request("user_led", 2).eq(plat.request("io_leds", 2)),
    plat.request("user_led", 3).eq(plat.request("io_leds", 3)),
]

plat.build(module, source=False)
prog = XC3SProg("ftdi")
prog.load_bitstream("build/top.bit")
