import argparse
import datetime
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .terminal_formatting import parse_color, bg_rgb_start, color_end
from .version import program_version

PROGRAM_NAME = "whatsapp-trend-plotter"
NR = "[0-9]{1,2}"
MESSAGE_RE = re.compile(rf"({NR}/{NR}/{NR}\s*,\s*{NR}:{NR})\s*-\s*(\+?[\s0-9]+)\s*:\s*(\S(?:.|\r?\n\D)*)")

log = logging.getLogger(PROGRAM_NAME)
console = logging.StreamHandler()
log.addHandler(console)
log.setLevel(logging.DEBUG)
console.setFormatter(
    logging.Formatter(parse_color("{asctime} [ℂ3.{levelname:>5}ℂ.] ℂ4.{name}ℂ.: {message}"),
                      style="{", datefmt="W%W %a %I:%M"))


@dataclass
class Message:
    time: datetime.datetime
    tel: str
    text: str


def get_matches(input_text, regex):
    for match in MESSAGE_RE.finditer(input_text):
        if regex is not None:
            if not regex.fullmatch(match.group(3)):
                continue

        yield Message(
            datetime.datetime.strptime(match.group(1).replace(" ", ""), "%m/%d/%y,%H:%M"),
            match.group(2),
            match.group(3),
        )


def command_entry_point():
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Program was interrupted by user")


def show_matches(matches, show):
    print(f"Found {len(matches)} entries")

    for message in matches:
        output = []
        if 1 in show:
            output.append(message.time)
        if 2 in show:
            output.append(f"[{message.tel}]")
        if 3 in show:
            output.append(message.text)

        print(*output, sep=" ")


def show_arbitrary_overview(matches, numeric, x: Callable, y: Callable, width, rows, columns=None):
    if columns is None:
        columns = [f"{i:2}" for i in range(width)]

    buckets = [[0] * width for _ in rows]

    for match in matches:
        buckets[y(match)][x(match)] += 1

    if numeric:
        # Print column headers
        print(" " * len(rows[0]), *columns)
        for r, b in zip(rows, buckets):
            print(r, *map(lambda n: f"{n:2}", b))
    else:
        maximum = max(max(l) for l in buckets)
        print(f"Maximum number per bucket: {maximum}")

        # Print column headers
        print(end=" " * len(rows[0]))
        for index, c in enumerate(columns):
            if index % 3 == 2:
                print(end=" " + c)
        print()

        def color(intensity):
            rel_int = int(intensity / maximum * 255)
            return bg_rgb_start(rel_int, 0, 255 - rel_int)

        for i, line in enumerate(buckets):
            print(end="Mo,Tu,We,Th,Fr,Sa,Su".split(",")[i])
            for value in line:
                print(end=color(value) + " ")
            print(color_end())


def show_week_overview(matches, numeric):
    show_arbitrary_overview(matches, numeric,
                            lambda m: m.time.hour, lambda m: m.time.weekday(), 24,
                            "Mo,Tu,We,Th,Fr,Sa,Su".split(","))


def show_annual_overview(matches, numeric):

    show_arbitrary_overview(matches, numeric,
                            lambda m: m.time.isocalendar()[1], lambda m: m.time.weekday(), 53,
                            "Mo,Tu,We,Th,Fr,Sa,Su".split(","))


def main():
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME,
                                     description="I was interested when people were washing their laundry in my apartment complex. "
                                                 "This matches a regex against an exported whatsapp chat to produce an overview of matches over time.",
                                     allow_abbrev=True, add_help=True, exit_on_error=True)

    parser.add_argument('-v', '--verbose', action='store_true', help="Show more output")
    parser.add_argument("--version", action="store_true", help="Show the current version of the program")
    parser.add_argument("-r", "--regex", help="Select only messages matches the python regex")
    parser.add_argument("-s", "--show", default="1,2,3",
                        help="What data to show for each message: 1 for time, 2 for telephone number and 3 for text. (1,2,3 is the default)")
    parser.add_argument("-w", "--week-overview", action="store_true",
                        help="Show an overview of when in the week the matches happen.")
    parser.add_argument("-a", "--annual-overview", action="store_true",
                        help="Show an overview of when in the year the matches happen.")
    parser.add_argument("-n", "--numeric", action="store_true",
                        help="Show the week overview with concrete numbers instead of colors")
    parser.add_argument("INPUT", help="Export file to parse")

    args = parser.parse_args()

    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    log.debug("Starting program...")

    if args.version:
        log.info(f"{PROGRAM_NAME} version {program_version}")
        return

    regex = None if args.regex is None else re.compile(args.regex, re.DOTALL | re.IGNORECASE)
    show = set(map(int, args.show.split(",")))
    matches = list(get_matches(Path(args.INPUT).read_text(), regex))

    if args.annual_overview:
        show_annual_overview(matches, args.numeric)
    elif args.week_overview:
        show_week_overview(matches, args.numeric)
    else:
        show_matches(matches, show)
