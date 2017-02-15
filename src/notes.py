
TONES = ['C', 'Cs', 'D', 'Ds', 'E', 'F', 'Fs', 'G', 'Gs', 'A', 'As', 'B']


def get_octave(note_number):
    return note_number // len(TONES)


def get_tone(note_number, octave):
    return TONES[note_number - octave * len(TONES)]


class Note:

    # TODO add length and other things
    def __init__(self, note_number):
        self.note_number = note_number
        self.octave = get_octave(note_number)
        self.tone = get_tone(note_number, self.octave)

