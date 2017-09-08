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
                        help='Path to directory where videos of the instruments can be found',
                        required=True)
    parser.add_argument('-i', '--instruments', help='Get the instruments', action='store_true')

    args = parser.parse_args()

    midifile = args.midifile
    if not os.path.isfile(midifile):
        parser.error("MIDI file \"{}\" not found".format(midifile))

    source_dir = args.source
    if not os.path.isdir(source_dir):
        parser.error("Source directory \"{}\" not found".format(source_dir))

    pattern = midi.read_midifile(midifile)
    pattern.make_ticks_abs()

    instrument_clips = {}

    if args.instruments:
        print_instruments(pattern)
    else:
        # load the clips for the tones that each instrument plays
        instruments = midiparse.get_instruments(pattern)
        for instrument_name in instruments:
            instrument_clips[instrument_name] = {}
            for note_number in instruments[instrument_name]:
                note_str = midiparse.note_number_to_note_string(note_number)
                file_name = os.path.join(source_dir, instrument_name,
                                         note_str + ".mp4")
                if not os.path.isfile(file_name):
                    error("The required file \"{}\" couldn't be found"
                          .format(file_name))

                instrument_clips[instrument_name][note_number] = \
                    edit.VideoFileClip(file_name)

        final_clip = videocomposing.compose(instrument_clips, pattern)

    sys.exit(0)


def error(msg):
    print "{red}ERROR: {end}\n\n{end}{yellow}{msg}{end}".format(red=TERM_FAIL,
                                                                end=TERM_ENDC,
                                                                yellow=TERM_WARNING,
                                                                msg=msg)
    sys.exit(-1)

if __name__ == "__main__":
    main()

