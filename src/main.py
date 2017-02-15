#!/usr/bin/python

import midi
import argparse
import os
import midiparse
import notes


def print_instruments(pattern):
    instruments = midiparse.get_instruments(pattern)
    song_name = midiparse.get_song_name(pattern)
    
    if song_name is not None:
        print "Song \'{}\':".format(song_name)

    print "Contains {} instruments\n".format(len(instruments))
    for instrument in instruments:
        print "Instrument \'{}\' plays these tones:".format(instrument)
        for note in instruments[instrument]:
            octave = notes.get_octave(note)
            tone = notes.get_tone(note, octave)
            print tone + str(octave)
        print ""


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--midifile', type=str, help='The MIDI file', required=True)
    parser.add_argument('-i', '--instruments', help='Get the instruments', action='store_true')

    args = parser.parse_args()

    midifile = args.midifile
    if not os.path.isfile(midifile):
        parser.error("MIDI file \"{}\" not found".format(midifile))


    pattern = midi.read_midifile(midifile)

    if args.instruments:
        print_instruments(pattern)

    # print pattern

if __name__ == "__main__":
    main()

