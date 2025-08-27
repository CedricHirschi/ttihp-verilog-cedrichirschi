# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

from xml.parsers.expat import errors
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Edge

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

TIMEOUT = 20


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    dut._log.info("Test project behavior")

    TIMEOUT = 200  # give it breathing room

    target_value = 0  # shared

    async def auto_comparator():
        """Update comp (ui_in[1]) from DAC (uo_out) every clock edge."""
        while True:
            await Edge(dut.uo_out)

            dac_value = dut.uo_out.value.integer

            comp_bit = 1 if target_value >= dac_value else 0  # 1 => HIGH

            dut._log.debug(f"Auto comparator: target={target_value} dac={dac_value} comp={comp_bit}")

            # rebuild: bit0=start, bit1=comp, upper bits unchanged
            prev_in = dut.ui_in.value.integer
            if comp_bit:
               dut.ui_in.value = prev_in | 0b10
            else:
               dut.ui_in.value = prev_in & ~0b10

    async def test_input_output(inp):
        nonlocal target_value
        target_value = inp

        # pulse START (bit0)
        prev_in = dut.ui_in.value.integer
        dut.ui_in.value = prev_in | 0b01
        await ClockCycles(dut.clk, 2)
        prev_in = dut.ui_in.value.integer
        dut.ui_in.value = prev_in & ~0b01

        last = dut.uio_out.value.integer
        for _ in range(TIMEOUT):
            await ClockCycles(dut.clk, 1)
            val = dut.uio_out.value.integer

            # # Reverse bit-order (8-bit value)
            # val = ((val & 0x01) << 7) | ((val & 0x02) << 5) | ((val & 0x04) << 3) | ((val & 0x08) << 1) | \
            #       ((val & 0x10) >> 1) | ((val & 0x20) >> 3) | ((val & 0x40) >> 5) | ((val & 0x80) >> 7)

            if val != last:
                # clear inputs only where appropriate; don't nuke upper bits
                # (adjust if your DUT needs a specific idle)
                return val
            last = val
        return None  # timed out

    comp_task = cocotb.start_soon(auto_comparator())

    expecteds = []
    results = []
    for i in range(256):
        expecteds.append(i)
        result = await test_input_output(i)
        results.append(result)
        await ClockCycles(dut.clk, 10)

    comp_task.kill()

    dut._log.info(f"{results=}")
    dut._log.info(f"{expecteds=}")

    errors = [((result if result is not None else 0) - expected) for result, expected in zip(results, expecteds)]
    dut._log.info(f"{errors=}")

    if plt is not None:
        plt.figure(figsize=(12, 6))
        plt.subplot(2, 1, 1)
        plt.plot(expecteds, results, 'o-')
        plt.ylabel("Output")
        plt.grid()
        plt.subplot(2, 1, 2)
        plt.plot(expecteds, errors, 'o-')
        plt.xlabel("Input")
        plt.ylabel("Error")
        plt.grid()
        plt.savefig("test_output.png")

    # dut.ui_in = 0b0000_0001 # Set CS high, the rest low
    # await ClockCycles(dut.clk, 1)
    # assert dut.uo_out.value == 0b1110_0001

    # Keep testing the module by changing the input values, waiting for
    # one or more clock cycles, and asserting the expected output values.
