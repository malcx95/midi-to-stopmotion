import moviepy.editor as edit
import pdb
import midiparse


def compose(instrument_clips, midipattern):
    tempo = midiparse.get_tempo(midipattern)
    track_clips = []
    for track in midipattern[1:]:
        name = midiparse.get_instrument_name(track)
        if name is None:
            # FIXME this is ugly
            name = "Untitled Instrument 1"
        track_clips.append(_process_track(instrument_clips[name],
                                          track, tempo))


def _process_track(clips, midi_track, tempo):
    """
    Composes one midi track into a stop motion video clip.
    Returns a CompositeVideoClip.
    """
    parsed_clips = []
    parsed_notes, parsed_events, max_simultaneous_notes = \
            midiparse.analyse_track(midi_track)
    pdb.set_trace()
    for note in parsed_notes:
        note_number = note.note_number
        clip = clips[note_number].copy()
        # TODO set clip start

