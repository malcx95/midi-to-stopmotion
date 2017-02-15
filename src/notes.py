

TONES = ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Gs', 'A', 'As', 'B']

class Note:

    # TODO add length and other things
    def __init__(self, note_number):
        self.note_number = note_number
        self.octave = _get_octave(note_number)
        self.tone = _get_tone(note_number, self.octave)


def _get_octave(note_number):
    return note_number // len(TONES)

def _get_tone(note_number, octave):
    return TONES[note_number - octave * len(TONES)]
