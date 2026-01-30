from _ctypes import ArgumentError

import zahlwort2num as w2n
import sys


def main():
    if len(sys.argv) > 1 and sys.argv[1]:
        try:
            result = w2n.convert(sys.argv[1])
            print(result)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        raise ArgumentError(None, "Usage: zahlwort2num-convert <german_number_words>")
