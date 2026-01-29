# main entry point

import sys
import argparse
from .dem import demo
from .gum import display

if __name__ == '__main__':
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--demo', type=str, help='the demo to run', default=None)
    parser.add_argument('-s', '--size', type=int, help='the size of the display', default=50)
    parser.add_argument('-t', '--theme', type=str, help='the theme to use', default='dark')
    args = parser.parse_args()

    # dispatch commands
    elem = demo(args.demo) if args.demo is not None else sys.stdin.read()
    display(elem, size=args.size, theme=args.theme)
