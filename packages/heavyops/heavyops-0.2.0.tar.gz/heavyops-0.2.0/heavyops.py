import sys
import runpy
from collections import Counter
from types import CodeType
import opcode
import argparse
import re

ops = (
    "MAKE_FUNCTION",
    "BUILD_TUPLE",
    "BUILD_LIST",
    "BUILD_SET",
    "BUILD_MAP",
    "LOAD_DEREF",
)


class InstructionCounter:
    def __init__(self, ops_codes: set[int], file_filter: re.Pattern | None = None):
        self.ops_codes = ops_codes
        self.file_filter = file_filter
        self.counts: Counter[tuple[CodeType, int]] = Counter()
        self.total = 0

    def on_instruction(self, code: CodeType, instruction_offset: int) -> None:
        self.total += 1
        if code.co_code[instruction_offset] in self.ops_codes:
            self.counts[(code, instruction_offset)] += 1

    def on_py_start(self, code: CodeType, instruction_offset: int) -> None:
        if not self.file_filter.search(code.co_filename):
            return
        sys.monitoring.set_local_events(
            sys.monitoring.PROFILER_ID, code, sys.monitoring.events.INSTRUCTION
        )

def main():
    parser = argparse.ArgumentParser(
        description="Profile heavy bytecode ops in a target script"
    )
    parser.add_argument(
        "-f",
        "--file-filter",
        metavar="PAT",
        help="Restrict file names to those matching this regex pattern.",
    )
    parser.add_argument(
        "-i",
        "--include",
        action="append",
        metavar="OP",
        help="Opcode name to track (can be repeated). Defaults to built-in list.",
    )
    parser.add_argument("target_script", help="Path to the target Python script to run")
    parser.add_argument(
        "script_args", nargs=argparse.REMAINDER, help="Arguments for the target script"
    )

    args = parser.parse_args()

    includes = args.include if args.include is not None else list(ops)
    invalid = [name for name in includes if name not in opcode.opmap]
    if invalid:
        print(f"Unknown opcode name(s): {', '.join(invalid)}", file=sys.stderr)
        sys.exit(2)

    ops_codes = {opcode.opmap[name] for name in includes}
    file_filter = re.compile(args.file_filter) if args.file_filter else None

    target_script = args.target_script
    sys.argv = [target_script] + args.script_args

    tool_id = sys.monitoring.PROFILER_ID
    sys.monitoring.use_tool_id(tool_id, "HeavyOpsProfiler")
    counter = InstructionCounter(ops_codes, file_filter)

    sys.monitoring.register_callback(
        tool_id, sys.monitoring.events.INSTRUCTION, counter.on_instruction
    )

    if file_filter:
        sys.monitoring.set_events(tool_id, sys.monitoring.events.PY_START)
        sys.monitoring.register_callback(
            tool_id, sys.monitoring.events.PY_START, counter.on_py_start
        )
    else:
        sys.monitoring.set_events(tool_id, sys.monitoring.events.INSTRUCTION)

    try:
        runpy.run_path(target_script, run_name="__main__")
    finally:
        sys.monitoring.set_events(tool_id, 0)
        report(counter.counts, counter.total)


def report(counts: Counter[tuple[CodeType, int]], total: int):
    print(f"{sum(counts.values()):,} / {total:,} tracked instructions", file=sys.stderr)

    instr_counts: Counter[int] = Counter()
    for (code, instruction_offset), count in counts.items():
        instr_counts[code.co_code[instruction_offset]] += count

    print(f"\n{'COUNT':<8} | {'INSTRUCTION'}", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    for op_code, count in instr_counts.most_common():
        print(f"{count:8,} | {opcode.opname[op_code]}", file=sys.stderr)

    print(f"\n{'COUNT':<8} | {'LOCATION'}", file=sys.stderr)
    print("-" * 50, file=sys.stderr)

    for (code, instruction_offset), count in counts.most_common(50):
        op_code = code.co_code[instruction_offset]
        pos_list = list(code.co_positions())
        idx = instruction_offset // 2
        line_no = pos_list[idx][1]
        location = (
            f"{code.co_filename}:{line_no} {code.co_name} {opcode.opname[op_code]}"
        )
        print(f"{count:8,} | {location}", file=sys.stderr)


if __name__ == "__main__":
    main()
