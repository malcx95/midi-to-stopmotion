
TONES = ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Gs', 'A', 'As', 'B']

class Note:

    # TODO add length and other things
    def __init__(self, note_number):
        self.note_number = note_number
        self.octave = _get_octave(note_number)
        self.tone = _get_tone(note_number)


def _get_octave(note_number):
    # TODO implement
    return 0

def _get_tone(note_number):
    # TODO implement
    return TONES[0]

