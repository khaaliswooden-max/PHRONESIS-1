"""Mercury Subleq emulator and safety-critical control loops.

HF-10 implementation: O2/CO2/pressure/thermal control loops run on a single-
instruction-set virtual machine (subleq). Single ISA = small formal-verification
surface; deterministic execution = WCET-bounded.

v0.1 status: emulator + WCET harness + working O2 control loop.
Formal Coq/Lean proofs of loop correctness are SPECULATIVE for v0.1 — flagged
in benchmark results.
"""

from dataclasses import dataclass
from typing import List, Tuple


class SubleqHalt(Exception):
    """Normal kernel halt via jump-to-negative."""


class SubleqWCETExceeded(Exception):
    """Kernel exceeded its WCET budget. Watchdog should trip."""


@dataclass
class SubleqResult:
    cycles: int
    memory: List[int]
    halted_normally: bool


class SubleqVM:
    """Single-instruction-set virtual machine.

    Instruction: subleq a b c
      memory[b] := memory[b] - memory[a]
      if memory[b] <= 0: pc := c   else: pc += 3

    Halt convention: jumping to a negative address halts the machine normally.
    """

    def __init__(self, memory: List[int], wcet_cycles: int = 10_000):
        self.memory = list(memory)
        self.wcet_cycles = wcet_cycles

    def run(self) -> SubleqResult:
        pc = 0
        cycles = 0
        while pc >= 0:
            if cycles >= self.wcet_cycles:
                raise SubleqWCETExceeded(f"exceeded {self.wcet_cycles} cycles")
            if pc + 2 >= len(self.memory):
                raise SubleqHalt("pc out of range")
            a = self.memory[pc]
            b = self.memory[pc + 1]
            c = self.memory[pc + 2]
            if a >= len(self.memory) or b >= len(self.memory):
                raise SubleqHalt(f"data address out of range: a={a} b={b}")
            self.memory[b] = self.memory[b] - self.memory[a]
            if self.memory[b] <= 0:
                pc = c
            else:
                pc += 3
            cycles += 1
        return SubleqResult(cycles=cycles, memory=self.memory, halted_normally=True)


def assemble_o2_valve_loop(setpoint_idx: int, reading_idx: int, command_idx: int, scratch_idx: int) -> List[int]:
    """Assemble a subleq program that computes command = setpoint - reading.

    Subleq idioms:
      - `subleq Z Z target` is an unconditional jump (memory[Z]-memory[Z]=0 <= 0 always).
      - Setting c-field = pc+3 makes the conditional branch fall-through identical:
        both branches lead to pc+3 either way, so the program is effectively linear
        regardless of input signs.

    Program (5 instructions, 15 program words):
      pc=0:  command -= reading              c=3
      pc=3:  scratch -= scratch (zero)       c=6
      pc=6:  scratch -= setpoint             c=9
      pc=9:  command -= scratch              c=12   (command = -reading - (-setpoint) = setpoint - reading)
      pc=12: scratch -= scratch (UNCOND)     c=-1   (always halts: 0 <= 0)
    """
    halt = -1
    program = [
        reading_idx, command_idx, 3,
        scratch_idx, scratch_idx, 6,
        setpoint_idx, scratch_idx, 9,
        scratch_idx, command_idx, 12,
        scratch_idx, scratch_idx, halt,
    ]
    return program


def build_o2_control_program(setpoint: int, reading: int, wcet_cycles: int = 100) -> SubleqVM:
    """Build a ready-to-run VM for an O2 valve control decision.

    Memory layout (positions 0-14 = program; 15-18 = data):
      15: setpoint  (input)
      16: reading   (input)
      17: command   (output; init 0)
      18: scratch   (init 0)
    """
    setpoint_idx, reading_idx, command_idx, scratch_idx = 15, 16, 17, 18
    program = assemble_o2_valve_loop(setpoint_idx, reading_idx, command_idx, scratch_idx)
    memory = program + [setpoint, reading, 0, 0]
    return SubleqVM(memory, wcet_cycles=wcet_cycles)


def measure_wcet(setpoints: List[int], readings: List[int], wcet_budget: int = 1000) -> Tuple[int, int]:
    """Run the O2 control loop across many input pairs and return (worst_cycles, total_runs).

    HF-10 WCET measurement function.
    """
    worst = 0
    for s, r in zip(setpoints, readings):
        vm = build_o2_control_program(s, r, wcet_cycles=wcet_budget)
        try:
            res = vm.run()
            if res.cycles > worst:
                worst = res.cycles
        except SubleqWCETExceeded:
            return wcet_budget + 1, len(setpoints)
    return worst, len(setpoints)
