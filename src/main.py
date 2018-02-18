#!/usr/bin/python

import midi
import argparse
import pdb
import sys
import os
import midiparse
import videocomposing
import moviepy.editor as edit


TERM_HEADER = '\033[95m'
TERM_OKBLUE = '\033[94m'
TERM_OKGREEN = '\033[92m'
TERM_WARNING = '\033[93m'
TERM_FAIL = '\033[91m'
TERM_ENDC = '\033[0m'
TERM_BOLD = '\033[1m'
TERM_UNDERLINE = '\033[4m'


def print_instruments(pattern):
    instruments = midiparse.get_instruments(pattern)
    song_name = midiparse.get_song_name(pattern)
    
    if song_name is not None:
        print "Song \'{}\':".format(song_name)

    print "Contains {} instruments\n".format(len(instruments))
    for instrument in instruments:
        print "Instrument \'{}\' plays these tones:".format(instrument)
        for note in instruments[instrument]:
            print midiparse.note_number_to_note_string(note)
        print ""


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-m', '--midifile', type=str, help='The MIDI file', required=True)
    parser.add_argument('-s', '--source', type=str,
                        help='Path to directory where videos of the instruments can be found')
    parser.add_argument('-a', 
                        '--auto',
                        help='Automatically analyse the video and extract notes',
                        action='store_true')
    parser.add_argument('-i', '--instruments', help='Get the instruments', action='store_true')
    parser.add_argument('-d', '--one',
                       help='Use the only provided instrument for all instruments', action='store_true')

    args = parser.parse_args()

    midifile = args.midifile
    if not os.path.isfile(midifile):
        parser.error("MIDI file \"{}\" not found".format(midifile))

    source_dir = args.source
    if not args.instruments and not os.path.isdir(source_dir):
        parser.error("Source directory \"{}\" not found".format(source_dir))

    pattern = midi.read_midifile(midifile)
    pattern.make_ticks_abs()

    instrument_clips = {}

    if args.instruments:
        print_instruments(pattern)
    else:
        # load the clips for the tones that each instrument plays
        instruments = midiparse.get_instruments(pattern)

        final_clip = videocomposing.compose(instruments, pattern,
                                           1920, 1080, source_dir)
        final_clip.write_videofile('output.mp4')

    sys.exit(0)


def error(msg):
    print "{red}ERROR: {end}\n\n{end}{yellow}{msg}{end}".format(red=TERM_FAIL,
                                                                end=TERM_ENDC,
                                                                yellow=TERM_WARNING,
                                                                msg=msg)
    sys.exit(-1)

if __name__ == "__main__":
    main()

