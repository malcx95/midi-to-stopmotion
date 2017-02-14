#!/usr/bin/python

import midi
import argparse
import os

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--midifile', type=str, help='The MIDI file', required=True)
    parser.add_argument('-i', '--instruments', help='Get the instruments', required=False)

    args = parser.parse_args()

    midifile = args.midifile
    if not os.path.isfile(midifile):
        parser.error("MIDI file \"{}\" not found".format(midifile))

    p = midi.read_midifile(midifile)
    print p

if __name__ == "__main__":
    main()

