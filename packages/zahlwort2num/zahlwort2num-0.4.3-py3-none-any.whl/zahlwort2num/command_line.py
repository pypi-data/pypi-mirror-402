from _ctypes import ArgumentError

import zahlwort2num as w2n
import sys


def main():
    # Debug: print what we're getting
    print(f"sys.argv: {sys.argv}, len: {len(sys.argv)}")
    if (len(sys.argv) > 1) and sys.argv[1]:
        print(f"Trying to convert: {sys.argv[1]}")
        print(w2n.convert(sys.argv[1]))
    else:
        print("No parameter given, raising ArgumentError")
        raise ArgumentError('No parameter given!')
