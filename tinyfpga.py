#!/usr/bin/env python3

import sys
import struct
from collections import OrderedDict

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform

from litex.build.lattice.programmer import TinyFpgaBProgrammer

from migen import *
from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import *

from litex.soc.cores.uart import UARTWishboneBridge

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litescope import LiteScopeAnalyzer


_io = [
    ("clk16", 0, Pins("B4"), IOStandard("LVCMOS33")),
    ("rst", 0, Pins("E1"), IOStandard("LVCMOS33")),

    ("serial", 0,
        Subsignal("tx", Pins("A1")),
        Subsignal("rx", Pins("A2")),
        IOStandard("LVCMOS33")
    ),
    ("user_led", 0, Pins("B1"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("C1"), IOStandard("LVCMOS33")),
    ("user_led", 2, Pins("D1"), IOStandard("LVCMOS33")),
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
        return [0]


class _CRG(Module):
    def __init__(self, platform):
        clk16 = platform.request("clk16")
        rst = platform.request("rst")
        self.clock_domains.cd_por = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys = ClockDomain()
        reset_delay = Signal(12, reset=4095)
        self.comb += [
            self.cd_por.clk.eq(clk16),
            self.cd_sys.clk.eq(clk16),
            self.cd_sys.rst.eq(reset_delay != 0)
        ]
        self.sync.por += \
            If(rst,
                reset_delay.eq(0)
            ).Elif(reset_delay != 0,
                reset_delay.eq(reset_delay - 1)
            )


class TinyFPGAB(SoCCore):
    def __init__(self, with_cpu=True):
        platform = Platform()
        sys_clk_freq = int(16e6)

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
            self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), sys_clk_freq, baudrate=9600))
            self.add_wb_master(self.cpu_or_bridge.wishbone)

        led_counter = Signal(32)
        self.sync += led_counter.eq(led_counter + 1)
        self.comb += [
            platform.request("user_led", 0).eq(led_counter[22]),
            platform.request("user_led", 1).eq(led_counter[23]),
            platform.request("user_led", 2).eq(led_counter[24])
        ]


def generate_design(**kwargs):
    soc = TinyFPGAB()
    builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv", **kwargs)
    builder.build()

def generate_firmware():
    os.system("cd firmware && make clean all")

def main():
    args = sys.argv[1:]
    flash = "flash" in args
    build = (not "flash" in args)

    if build:
        print("[building]...")
        generate_design(compile_gateware=False) # generate software headers
        generate_firmware()                     # compile firmware
        generate_design()                       # generate design with embedded firmware
    else:
        print("[flashing]...")
        prog = TinyFpgaBProgrammer()
        prog.flash(0x30000, "build/gateware/top.bin")

if __name__ == "__main__":
    main()
