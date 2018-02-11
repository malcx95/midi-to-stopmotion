import moviepy.editor as edit
import pdb
import midiparse

# TODO remove
class VideoNote:

    def __init__(self, note, clip):
        self.note = note
        self.clip = clip
        

def compose(instrument_clips, midipattern):
    tempo = midiparse.get_tempo(midipattern)
    # TODO you have to multiply the times in analyze track
    # with the tempo and time signature
    track_clips = []
    for track in midipattern[1:]:
        track_clips.append(_process_track(instrument_clips, track, tempo))
        pdb.set_trace()


def _process_track(instrument_clips, midi_track, tempo):
    """
    Composes one midi track into a stop motion video clip.
    Returns a CompositeVideoClip.
    """
    clips = []
    parsed_notes = midiparse.analyse_track(track)
    for note in parsed_notes:
        note_number = note.note_number
        clip = instrument_clips[note_number].copy()
        # TODO set clip start

