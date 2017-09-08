import moviepy.editor as edit
import pdb
import midiparse


class VideoNote:

    def __init__(self, note, clip):
        self.note = note
        self.clip = clip
        

def compose(instrument_clips, midipattern):
    tempo = midiparse.get_tempo(midipattern)
    # TODO you have to multiply the times in analyze track
    # with the tempo and time signature
    for track in midipattern[1:]:
        parsed_notes = midiparse.analyse_track(track)
        pdb.set_trace()

