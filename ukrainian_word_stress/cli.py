import argparse
import fileinput
import logging
from ukrainian_word_stress import Stressifier, StressSymbol


def main():
    parser = argparse.ArgumentParser(
        description="Add stress mark to texts in Ukrainian"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--on-ambiguity", choices=["skip", "first", "all"], default='skip')
    parser.add_argument(
        "--symbol",
        default="acute",
        help=("Which stress symbol to use. Default is `acute`. "
              "Another option is `combining`. Custom values are allowed."),
    )
    parser.add_argument(
        "path", nargs="*", help="File(s) to process. If not set, read from stdin"
    )
    args = parser.parse_args()

    if args.version:
        print("ukrainian-word-stress 0.0.1")
        return

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    if args.symbol == "acute":
        args.symbol = StressSymbol.AcuteAccent
    elif args.symbol == "combining":
        args.symbol = StressSymbol.CombiningAcuteAccent

    stressify = Stressifier(stress_symbol=args.symbol, on_ambiguity=args.on_ambiguity)
    for line in fileinput.input(args.path):
        print(stressify(line), end="")


if __name__ == "__main__":
    main()
