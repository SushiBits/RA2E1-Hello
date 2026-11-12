#!/usr/bin/env python3
"""Generate the interrupt handler table used by the vector table and stubs.

The input is either a CMSIS device header (the ``IRQn_Type`` enum SVDConv
writes) or the CMSIS-SVD that header was generated from; the format is
detected from the content, so either file can be passed in.

The output is the conditional header ``platform/src/LKS32MC03x_it.c`` includes
three times with a different ``IRQN_HANDLER``/``SKIP_HANDLER``::

    /* This file is auto-generated using the IRQN tool. Do not modify. */

    #ifndef IRQN_HANDLER

    #include "LKS32MC03x_it.h"

    #else

    IRQN_HANDLER(-14, NonMaskableInt)
    ...
    SKIP_HANDLER(-6)
    ...

    #endif

Every slot from IRQ --start up to the highest interrupt the device defines is
emitted, and gaps become ``SKIP_HANDLER()``, because the vector table has to
stay dense.

An SVD only lists device interrupts, so reading one synthesises the Cortex-M
core exceptions from its ``<cpu>`` element (that is what SVDConv does too);
``--no-core`` suppresses that.

Examples::

    python3 irqn.py LKS32MC03x_it.h -i platform/include/LKS32MC03x.h -o out.h
    python3 irqn.py LKS32MC03x_it.h -i platform/share/LKS32MC03x.svd -o out.h
    python3 irqn.py '"LKS32MC03x_it.h"' < platform/include/LKS32MC03x.h > out.h
    python3 irqn.py -i platform/share/LKS32MC03x.svd --list
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET

PROG = "irqn"

_quiet = False
_verbose = False


class ToolError(Exception):
    """A fatal condition, reported to the user without a traceback."""


def warn(message: str) -> None:
    if not _quiet:
        print(f"{PROG}: warning: {message}", file=sys.stderr)


def info(message: str) -> None:
    if _verbose:
        print(f"{PROG}: {message}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------


def read_input(path: str | None) -> str:
    try:
        if path in (None, "-"):
            buffer = getattr(sys.stdin, "buffer", None)
            data = buffer.read() if buffer is not None else sys.stdin.read().encode()
        else:
            with open(path, "rb") as handle:
                data = handle.read()
    except OSError as exc:
        raise ToolError(f"cannot read {path or 'stdin'}: {exc}") from exc
    try:
        return data.decode("utf-8-sig")  # tolerate a UTF-8 BOM
    except UnicodeDecodeError as exc:
        raise ToolError(f"{path or 'stdin'} is not valid UTF-8: {exc}") from exc


def to_int(text: str) -> int:
    """Parse a decimal or 0x-prefixed integer, as found in SVDs and headers."""
    token = text.strip()
    negative = token.startswith("-")
    digits = token.lstrip("+-")
    value = int(digits, 16) if digits[:2].lower() == "0x" else int(digits, 10)
    return -value if negative else value


# ---------------------------------------------------------------------------
# Device header
# ---------------------------------------------------------------------------

_INT = r"(?:0[xX][0-9A-Fa-f]+|\d+)"
_HEADER_ENUM = re.compile(
    r"^[ \t]*([A-Za-z_]\w*)_IRQn[ \t]*=[ \t]*(-?" + _INT + r")", re.MULTILINE
)
_HEADER_DEFINE = re.compile(
    r"^[ \t]*#[ \t]*define[ \t]+([A-Za-z_]\w*)_IRQn[ \t]+(-?" + _INT + r")",
    re.MULTILINE,
)


def parse_header(text: str) -> list[tuple[int, str]]:
    """Collect ``NAME_IRQn = value`` entries from a CMSIS device header."""
    entries = [(to_int(value), name) for name, value in _HEADER_ENUM.findall(text)]
    if not entries:
        entries = [(to_int(value), name) for name, value in _HEADER_DEFINE.findall(text)]
    return entries


# ---------------------------------------------------------------------------
# CMSIS-SVD
# ---------------------------------------------------------------------------


def local_name(tag: str) -> str:
    """Strip the ``{namespace}`` part ElementTree keeps."""
    return tag.rpartition("}")[2]


def children(element, name: str) -> list:
    return [child for child in element if local_name(child.tag) == name]


def child_text(element, name: str) -> str | None:
    for child in element:
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return None


def direct_interrupts(peripheral) -> list[tuple[int, str]]:
    found = []
    for interrupt in children(peripheral, "interrupt"):
        name = child_text(interrupt, "name")
        raw = child_text(interrupt, "value")
        if not name:
            warn("skipping an <interrupt> element without a <name>")
            continue
        if raw is None:
            warn(f"interrupt {name} has no <value>, skipped")
            continue
        try:
            found.append((to_int(raw), name))
        except ValueError:
            warn(f"interrupt {name} has value {raw!r}, which is not a number; skipped")
    return found


def interrupts_of(peripheral, peripherals: dict) -> list[tuple[int, str]]:
    """Interrupts of a peripheral, following derivedFrom as the SVD spec says."""
    seen = set()
    while peripheral is not None and id(peripheral) not in seen:
        seen.add(id(peripheral))
        found = direct_interrupts(peripheral)
        if found:
            return found
        base = peripheral.get("derivedFrom")
        peripheral = peripherals.get(base) if base else None
    return []


def parse_svd(text: str) -> tuple[str | None, list[tuple[int, str]]]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ToolError(f"input looks like XML but is not well formed: {exc}") from exc
    if local_name(root.tag) != "device":
        raise ToolError(
            f"expected an SVD <device> root element, found <{local_name(root.tag)}>"
        )

    cpu = None
    for element in children(root, "cpu"):
        cpu = child_text(element, "name") or cpu

    peripherals = {}
    for group in children(root, "peripherals"):
        for peripheral in children(group, "peripheral"):
            name = child_text(peripheral, "name")
            if name:
                peripherals.setdefault(name, peripheral)

    entries = []
    for peripheral in peripherals.values():
        entries.extend(interrupts_of(peripheral, peripherals))
    return cpu, entries


# ---------------------------------------------------------------------------
# Interrupt numbering
# ---------------------------------------------------------------------------

# Cortex-M core exceptions, named as in the CMSIS headers. The third field is
# the CPU generation that defines the exception:
# 0 = ARMv6-M (Cortex-M0/M0+), 3 = ARMv7-M (M3/M4/M7),
# 8 = ARMv8-M (M23/M33/M35P/M55/M85).
_CORE_EXCEPTIONS = (
    ("Reset", -15, 0),
    ("NonMaskableInt", -14, 0),
    ("HardFault", -13, 0),
    ("MemManage", -12, 3),
    ("BusFault", -11, 3),
    ("UsageFault", -10, 3),
    ("SVCall", -5, 0),
    ("DebugMon", -4, 3),
    ("SecureFault", -3, 8),
    ("PendSV", -2, 0),
    ("SysTick", -1, 0),
)

_CPU_GENERATIONS = {
    "CM0": 0,
    "CM0PLUS": 0,
    "CM0+": 0,
    "CM3": 3,
    "CM4": 3,
    "CM7": 3,
    "CM23": 8,
    "CM33": 8,
    "CM35P": 8,
    "CM55": 8,
    "CM85": 8,
}


def core_exceptions(cpu: str | None) -> list[tuple[int, str]]:
    key = (cpu or "").strip().upper().replace(" ", "").replace("_", "")
    if key.startswith("CORTEX-"):
        key = key[len("CORTEX-"):]
    generation = _CPU_GENERATIONS.get(key)
    if generation is None:
        warn(f"unknown CPU {cpu!r}, assuming a Cortex-M0 core")
        generation = 0
    return [(value, name) for name, value, since in _CORE_EXCEPTIONS if since <= generation]


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def collect(entries: list[tuple[int, str]], start: int) -> dict[int, str]:
    """Fold (number, name) pairs into {number: name}, keeping the first of each."""
    by_number: dict[int, str] = {}
    by_name: dict[str, int] = {}
    for number, name in entries:
        if number < start:
            continue  # Reset and anything below the first core exception
        if not _IDENTIFIER.match(name):
            raise ToolError(
                f"IRQ {number}: {name!r} is not a C identifier, "
                f"so it cannot name a {name}_IRQHandler"
            )
        if name in by_name:
            if by_name[name] != number:
                warn(
                    f"{name} appears at both IRQ {by_name[name]} and IRQ {number}; "
                    f"keeping IRQ {by_name[name]}"
                )
            continue
        if number in by_number:
            warn(
                f"IRQ {number} is claimed by both {by_number[number]} and {name}; "
                f"keeping {by_number[number]}"
            )
            continue
        by_number[number] = name
        by_name[name] = number
    return by_number


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

_BANNER = "/* This file is auto-generated using the IRQN tool. Do not modify. */\n"


def include_spec(argument: str) -> str:
    """Normalise the #include argument, quoting a bare header name."""
    spec = argument.strip()
    if len(spec) >= 2 and spec[0] in "\"<" and spec[-1] in "\">":
        return spec
    return f'"{spec}"'


def render(by_number: dict[int, str], include: str, start: int) -> str:
    lines = [
        _BANNER,
        "\n#ifndef IRQN_HANDLER\n\n",
        f"#include {include}\n\n",
        "#else\n\n",
    ]
    for number in range(start, max(by_number) + 1):
        name = by_number.get(number)
        if name is None:
            lines.append(f"SKIP_HANDLER({number})\n")
        else:
            lines.append(f"IRQN_HANDLER({number}, {name})\n")
    lines.append("\n#endif\n\n")
    return "".join(lines)


def write_output(path: str | None, text: str) -> None:
    if path in (None, "-"):
        stream = sys.stdout
        try:
            stream.reconfigure(newline="\n")  # keep LF on Windows too
        except (AttributeError, ValueError):
            pass
        stream.write(text)
        stream.flush()
        return
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError as exc:
        raise ToolError(f"cannot write {path}: {exc}") from exc


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Generate the IRQN_HANDLER/SKIP_HANDLER table for a vector "
        "table from a CMSIS device header or an SVD file.",
    )
    parser.add_argument(
        "include",
        nargs="?",
        metavar="INCLUDE",
        help='argument of the generated #include, e.g. "LKS32MC03x_it.h" or <cmsis.h>',
    )
    parser.add_argument(
        "-i", "--input", metavar="PATH",
        help="device header or SVD to read (default: stdin)",
    )
    parser.add_argument(
        "-o", "--output", metavar="PATH",
        help="write the table to PATH (default: stdout)",
    )
    parser.add_argument(
        "-f", "--format", choices=("auto", "header", "svd"), default="auto",
        help="input format (default: auto, i.e. XML means SVD)",
    )
    parser.add_argument(
        "-s", "--start", type=int, default=-14, metavar="IRQN",
        help="lowest IRQ number to emit (default: -14, NonMaskableInt)",
    )
    parser.add_argument(
        "--cpu", metavar="NAME",
        help="CPU name to use for an SVD instead of its <cpu> element",
    )
    parser.add_argument(
        "--no-core", action="store_true",
        help="do not add the Cortex-M core exceptions when reading an SVD",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="list IRQ numbers and names instead of generating the table",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress warnings")
    parser.add_argument("-v", "--verbose", action="store_true", help="describe the parse")
    return parser


def main(argv: list[str] | None = None) -> int:
    global _quiet, _verbose

    parser = build_parser()
    args = parser.parse_args(argv)
    _quiet = args.quiet
    _verbose = args.verbose

    if args.include is None and not args.list:
        parser.error("the INCLUDE argument is required unless --list is used")

    try:
        text = read_input(args.input)

        fmt = args.format
        if fmt == "auto":
            fmt = "svd" if text.lstrip().startswith("<") else "header"

        if fmt == "svd":
            cpu, entries = parse_svd(text)
            cpu = args.cpu or cpu
            info(f"read {len(entries)} interrupts from the SVD (cpu: {cpu or 'unknown'})")
            if not args.no_core:
                entries = core_exceptions(cpu) + entries
        else:
            entries = parse_header(text)
            info(f"read {len(entries)} IRQn entries from the header")

        if not entries:
            raise ToolError("no interrupt definitions found; expected a CMSIS header or SVD")

        by_number = collect(entries, args.start)
        if not by_number:
            raise ToolError(f"no interrupts at or above IRQ {args.start}")
        info(f"{len(by_number)} handlers, IRQ {args.start} to {max(by_number)}")

        if args.list:
            report = "".join(
                f"{number} {by_number[number]}\n" for number in sorted(by_number)
            )
        else:
            report = render(by_number, include_spec(args.include), args.start)

        write_output(args.output, report)
    except ToolError as exc:
        print(f"{PROG}: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
