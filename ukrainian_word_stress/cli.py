import argparse
import fileinput
import logging
from ukrainian_word_stress import stressify


def main():
    parser = argparse.ArgumentParser(description="Add stress mark to texts in Ukrainian")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("path", nargs="*", help="File(s) to process. If not set, read from stdin")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    for line in fileinput.input(args.path):
        print(stressify(line), end='')

if __name__ == "__main__":
    main()
