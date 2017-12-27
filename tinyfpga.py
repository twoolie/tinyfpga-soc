#!/usr/bin/env python3

import sys
import struct
from collections import OrderedDict

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform

from litex.gen import *
from litex.soc.interconnect.csr import *

from litex.soc.cores.uart import UARTWishboneBridge
from litex.soc.cores.timer import Timer

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from litescope import LiteScopeAnalyzer


_io = [
    ("clk16", 0, Pins("B4"), IOStandard("LVCMOS33")),
    ("serial", 0,
        Subsignal("tx", Pins("B2")),
        Subsignal("rx", Pins("A2")),
        IOStandard("LVCMOS33")
    ),
]


class Platform(LatticePlatform):
    default_clk_name = "clk16"
    default_clk_period = 62.5

    def __init__(self):
        LatticePlatform.__init__(self, "ice40-lp8k-cm81", _io, toolchain="icestorm")

    def create_programmer(self):
        return TinyFpgaBProgrammer()


def csr_map_update(csr_map, csr_peripherals):
    csr_map.update(OrderedDict((n, v)
        for v, n in enumerate(csr_peripherals, start=max(csr_map.values()) + 1)))


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


class TinyFPGA(SoCCore):
    csr_peripherals = [
        "flash",
        "analyzer"
    ]
    csr_map_update(SoCCore.csr_map, csr_peripherals)

    def __init__(self, with_cpu=False, with_analyzer=False):
        platform = Platform()
        sys_clk_freq = int(16e6)

        integrated_rom_size = 0
        integrated_rom_init = []
        if with_cpu:
            integrated_rom_size = 0x6000
            integrated_rom_init = get_firmware_data("./firmware/firmware.bin", 0x6000)

        SoCCore.__init__(self, platform,
            clk_freq=sys_clk_freq,
            cpu_type="lm32" if with_cpu else None,
            csr_data_width=32, csr_address_width=15,
            with_uart=with_cpu, uart_stub=with_analyzer,
            with_timer=with_cpu,
            ident="TinyFPGA Test SoC",
            ident_version=True,
            integrated_rom_size=integrated_rom_size,
            integrated_rom_init=integrated_rom_init,
            integrated_main_ram_size=0)

        # bridge
        if with_cpu:
            self.add_constant("ROM_BOOT_ADDRESS", self.mem_map["main_ram"])
        else:
            self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"), sys_clk_freq, baudrate=115200))
            self.add_wb_master(self.cpu_or_bridge.wishbone)

        # analyzer
        if with_analyzer:
            analyzer_signals = [
                Signal(),
                Signal()
            ]
            self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 512)

    def do_exit(self, vns):
        if hasattr(self, "analyzer"):
            self.analyzer.export_csv(vns, "test/analyzer.csv")


def main():
    print("[building]...")
    soc = TinyFPGA()
    builder = Builder(soc, csr_csv="test/csr.csv")
    vns = builder.build()
    soc.do_exit(vns)


if __name__ == "__main__":
    main()
