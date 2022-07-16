import fileinput
from ukrainian_stress import stressify


def main():
    for line in fileinput.input():
        print(stressify(line), end='')

if __name__ == "__main__":
    main()
