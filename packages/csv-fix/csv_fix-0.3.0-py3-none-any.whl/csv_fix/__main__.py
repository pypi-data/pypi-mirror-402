#!/usr/bin/env python3
"""CSV Converter - A command line tool for fixing malformed CSV file."""

import argparse
import os
import sys
import logging

from csv_fix import CSVStateMachine, FILE_END


def setup_logging():
    level = os.getenv("LOG_LEVEL", "WARNING").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.WARNING),
        format="%(levelname)s - %(name)s - %(message)s",
    )


def parse_args(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="csv_conv",
        description="CSV Converter - A tool for CSV file processing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-s",
        dest="separator",
        default=",",
        help="Define separator. Defaults to comma.",
    )

    parser.add_argument(
        "-q",
        dest="qualifier",
        default='"',
        help="Define text qualifier. Defaults to auto detect.",
    )

    parser.add_argument(
        "-t",
        dest="trim",
        action="store_true",
        default=False,
        help="Trim white space at the beginning and end of each field. Defaults to no trim.",
    )

    parser.add_argument(
        "-z",
        dest="timezone",
        default=None,
        help=(
            "Specify timezone for time fields. Defaults to server timezone. "
            "Can also be Asia/Chongqing etc. "
            "For standard timezone names, refer to: "
            "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
        ),
    )

    parser.add_argument(
        "-k",
        dest="skip_errors",
        action="store_true",
        default=False,
        help="Skip errors and continue parsing following lines.",
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input CSV file path. Read from stdin if not provided.",
    )

    return parser.parse_args(args)


def feed_input(fs, state_machine):
    """Feed input stream to state machine line by line."""
    for line in fs:
        state_machine.feed(line)
    # Indicate the end of input
    state_machine.feed(FILE_END)


def check_args(args):
    """Check validity of command line arguments."""
    if len(args.separator) != 1:
        logging.error("Separator must be a single character.")
        return False
    if len(args.qualifier) != 1 and args.qualifier is not None:
        logging.error("Qualifier can't be empty string.")
        return False
    return True


def main():
    """Main entry point."""
    args = parse_args()

    logger = logging.getLogger(__name__)
    if not check_args(args):
        return 1
    logger.info("Separator: %s", args.separator)
    logger.info(
        "Qualifier: %s",
        "[auto detect]" if args.qualifier is None else args.qualifier,
    )
    logger.info("Trim: %s", args.trim)
    logger.info("Timezone: %s", args.timezone)
    logger.info("Skip errors: %s", args.skip_errors)
    logger.info("Input file: %s", args.input_file or "stdin")
    state_machine = CSVStateMachine(args, sys.stdout)
    if sys.stdin.isatty():
        # Read from file
        filename = args.input_file
        try:
            with open(filename, "r", encoding="utf-8") as fs:
                feed_input(fs, state_machine)
        except IOError:
            logging.error("File not found or occupied by other process: %s", filename)
            return 1
    else:
        # Read from stdin
        fs = sys.stdin
        feed_input(fs, state_machine)
    return 0


if __name__ == "__main__":
    setup_logging()
    sys.exit(main())
