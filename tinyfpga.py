#!/usr/bin/env python3

import sys
import struct
from collections import OrderedDict

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform

from litex.build.lattice.programmer import TinyFpgaBProgrammer

from litex.gen import *
from litex.soc.interconnect.csr import *

from litex.soc.cores.uart import UARTWishboneBridge

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litescope import LiteScopeAnalyzer


_io = [
    ("clk16", 0, Pins("B4"), IOStandard("LVCMOS33")),
    ("serial", 0,
        Subsignal("tx", Pins("A1")),
        Subsignal("rx", Pins("A2")),
        IOStandard("LVCMOS33")
    ),
    ("user_led", 0, Pins("B1"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("C1"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("D1"), IOStandard("LVCMOS33")),
    ("user_led", 3, Pins("E1"), IOStandard("LVCMOS33")),
]


class Platform(LatticePlatform):
    def __init__(self):
        LatticePlatform.__init__(self, "ice40-lp8k-cm81", _io, toolchain="icestorm")

    def create_programmer(self):
        return TinyFpgaBProgrammer()


def get_firmware_data(filename, size):
    try:
        data = []
        with open(filename, "rb") as firmware_file:
            while True:
                w = firmware_file.read(4)
                if not w:
                    break
                data.append(struct.unpack(">I", w)[0])
        data_size = len(data)*4
        assert data_size > 0
        assert data_size < size, (
            "firmware is too big: {}/{} bytes".format(
                data_size, size))
        return data
    except:
        return []


class _CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain()
        clk16 = platform.request("clk16")
        pll_sys_clk = Signal()
        self.specials += Instance("SB_PLL40_CORE",
            i_REFERENCECLK=clk16,
            o_PLLOUTCORE=pll_sys_clk,
            i_RESETB=1,
            i_BYPASS=0
        )
        self.comb += self.cd_sys.clk.eq(pll_sys_clk)


class TinyFPGAB(SoCCore):
    def __init__(self, with_cpu=True):
        platform = Platform()
        sys_clk_freq = int(48e6)

        integrated_rom_size = 0
        integrated_rom_init = []
        if with_cpu:
            integrated_rom_size = 0x2000
            integrated_rom_init = get_firmware_data("./firmware/firmware.bin", 0x2000)

        SoCCore.__init__(self, platform,
            clk_freq=sys_clk_freq,
            cpu_type="lm32" if with_cpu else None,
            csr_data_width=8,
            with_uart=with_cpu, uart_baudrate=9600,
            with_timer=with_cpu,
            ident="TinyFPGA Test SoC",
            ident_version=True,
            integrated_rom_size=integrated_rom_size,
            integrated_rom_init=integrated_rom_init)

        self.submodules.crg = _CRG(platform)

        # bridge
        if not with_cpu:
            self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), sys_clk_freq, baudrate=115200))
            self.add_wb_master(self.cpu_or_bridge.wishbone)


        led_counter = Signal(32)
        self.sync += led_counter.eq(led_counter + 1)
        self.comb += [
            platform.request("user_led", 0).eq(led_counter[22]),
            platform.request("user_led", 1).eq(led_counter[23]),
            platform.request("user_led", 2).eq(led_counter[24]),
            platform.request("user_led", 3).eq(led_counter[25])
        ]


def main():
    args = sys.argv[1:]
    flash = "flash" in args
    build = (not "flash" in args)

    if build:
        print("[building]...")
        soc = TinyFPGAB()
        builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv")
        vns = builder.build()
        soc.do_exit(vns)
    else:
        print("[flashing]...")
        prog = TinyFpgaBProgrammer()
        prog.flash(0x30000, "build/gateware/top.bin")

if __name__ == "__main__":
    main()
