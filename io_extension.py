#!/usr/bin/env python3

# use arty as io extension for tinyfpgab

# io         |       arty      |   tinyfpgab
# serial tx  |    porta0 (G13) |   pin5  (A2)
# serial rx  |    porta1 (B11) |   pin6  (A1)
# led0       |    porta2 (A11) |   pin7  (B1)
# gnd        |                 |
# led1       |    porta3 (D12) |   pin8  (C1)
# led2       |    porta4 (D13) |   pin9  (D1)
# led3       |    porta5 (B18) |   pin10 (E1)

import sys

from litex.gen import *
from litex.build.xilinx import VivadoProgrammer
from litex.build.generic_platform import *
from litex.boards.platforms import arty

_extension_io = [
    ("io_serial", 0,
        Subsignal("tx", Pins("G13")),
        Subsignal("rx", Pins("B11")),
        IOStandard("LVCMOS33")
    ),
    ("io_leds", 0, Pins("A11"), IOStandard("LVCMOS33")),
    ("io_leds", 1, Pins("D12"), IOStandard("LVCMOS33")),
    ("io_leds", 2, Pins("D13"), IOStandard("LVCMOS33")),
    ("io_rst",  0, Pins("B18"), IOStandard("LVCMOS33")),
]


def main():
    args = sys.argv[1:]
    load = "load" in args
    build = (not "load" in args)

    if build:
        print("[building]...")
        plat = arty.Platform()
        plat.add_extension(_extension_io)
        module = Module()
        counter = Signal(32)
        module.sync += counter.eq(counter + 1)
        serial_pads = plat.request("serial")
        io_serial_pads = plat.request("io_serial")
        module.comb += [
            serial_pads.tx.eq(io_serial_pads.rx),
            io_serial_pads.tx.eq(serial_pads.rx),
            plat.request("user_led", 0).eq(plat.request("io_leds", 0)),
            plat.request("user_led", 1).eq(plat.request("io_leds", 1)),
            plat.request("user_led", 2).eq(plat.request("io_leds", 2)),
            plat.request("io_rst", 0).eq(plat.request("user_btn", 0)),
        ]
        plat.build(module, source=False)
    elif load:
        print("[loading]...")
        prog = VivadoProgrammer()
        prog.load_bitstream("build/top.bit")

if __name__ == "__main__":
    main()
