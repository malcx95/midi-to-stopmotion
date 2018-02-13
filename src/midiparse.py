import pdb
import midi

TONES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

DEFAULT_TEMPO = 500000

class TrackEvent:

    def __init__(self, time, num_simultaneous_notes):
        self.time = time
        self.num_simultaneous_notes = num_simultaneous_notes
        self.started_notes = []
        self.ended_notes = []

    def __repr__(self):
        return "{} simultaneous notes, {} started, {} ended\n".format(
            self.num_simultaneous_notes, 
            len(self.started_notes), len(self.ended_notes))


class Note:

    def __init__(self, note_number, start, end):
        self.note_number = note_number
        self.octave = note_number_to_octave(note_number)
        self.tone = note_number_to_tone(note_number, self.octave)
        self.start = start
        self.end = end
        self.duration = end - start
        self.video_position = None

    def __repr__(self):
        return "{}{} from {} to {} (duration: {})".format(self.tone, self.octave, 
                                                          self.start, self.end, self.duration)


def _event_pitch(event):
    return event.data[0]


def _event_vel(event):
    return event.data[1]


def _is_note_start(event):
    return isinstance(event, midi.NoteOnEvent) and _event_vel(event) != 0


def _is_note_end(event):
    return isinstance(event, midi.NoteOffEvent) or \
            (isinstance(event, midi.NoteOnEvent) and _event_vel(event) == 0)


def analyse_track(miditrack):
    """
    Converts a miditrack to a list of Notes and a dictionary of events
    """
    curr_events = []
    parsed_notes = []
    parsed_events = {}
    max_simultaneous_notes = 0
    for event in miditrack:
        if _is_note_start(event):
            curr_events.append(event)
        elif _is_note_end(event):
            for i in range(len(curr_events)):
                ev = curr_events[i]
                p = _event_pitch(ev)
                if _event_pitch(ev) == _event_pitch(event):
                    note = Note(p, ev.tick, event.tick)
                    parsed_notes.append(note)
                    curr_events.remove(ev)

                    curr_simultaneous_notes = \
                        _add_note_to_parsed_events(parsed_events, note)
                    max_simultaneous_notes = max(max_simultaneous_notes, 
                                                curr_simultaneous_notes)
                    break
    return parsed_notes, parsed_events, max_simultaneous_notes


def _add_note_to_parsed_events(parsed_events, note):
    start = note.start
    end = note.end
    num_simultaneous_notes = 1
    if start not in parsed_events:
        parsed_events[start] = TrackEvent(start, 1)
        parsed_events[start].started_notes.append(note)
    else:
        parsed_events[start].started_notes.append(note)
        parsed_events[start].num_simultaneous_notes += 1
        num_simultaneous_notes = parsed_events[start].num_simultaneous_notes
    note.video_position = num_simultaneous_notes - 1
    if end not in parsed_events:
        parsed_events[end] = TrackEvent(end, 0)
        parsed_events[end].ended_notes.append(note)
    else:
        parsed_events[end].ended_notes.append(note)
    return num_simultaneous_notes


def note_number_to_octave(note_number):
    return note_number // len(TONES)


def note_number_to_tone(note_number, octave):
    return TONES[note_number - octave * len(TONES)]


def note_number_to_note_string(note_number):
    octave = note_number_to_octave(note_number)
    tone = note_number_to_tone(note_number, octave)
    return tone + str(octave)


def get_tempo(midipattern):
    """Returns the tempo of the song in microseconds per beat"""
    for p in midipattern[0]:
        if isinstance(p, midi.SetTempoEvent):
            return p.get_mpqn()

    return DEFAULT_TEMPO



def get_instruments(midipattern):
    """
    Gets the a dictionary of the used instruments (tracks) in a midi pattern,
    mapped to the sorted list of unique note numbers that instrument plays.
    """
    result = {}
    i = 0
    for track in midipattern[1:]:
        i += 1
        name = get_instrument_name(track, i)
        result[name] = _extract_notes(track)
    return result


def _extract_notes(miditrack):
    """
    Gets sorted list of all unique note numbers in a midi track.
    """
    note_numbers = []
    for event in miditrack:
        if isinstance(event, midi.NoteOnEvent):
            note_number, velocity = event.data
            # velocity == 0 is equivalent to a note off event
            if velocity != 0 and not note_number in note_numbers:
                note_numbers.append(note_number)
    return sorted(note_numbers)


def get_instrument_name(miditrack, number=None):
    """
    Gets the instrument name (track name) of the midi track.
    """
    for event in miditrack:
        if isinstance(event, midi.TrackNameEvent):
            return event.text
    if number is not None:
        # FIXME this is ugly
        return "Untitled Instrument " + str(number)
    else:
        return None


def get_song_name(midipattern):
    """
    Gets the song name in the midi pattern.
    Returns None if no name was found.
    """
    for p in midipattern[0]:
        if isinstance(p, midi.TrackNameEvent):
            return p.text
    return None

