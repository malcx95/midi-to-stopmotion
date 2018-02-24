import pdb
import midi

TONES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

DEFAULT_TEMPO = 500000

class TrackEvent:

    def __init__(self, time, curr_notes):
        self.time = time
        self.num_simultaneous_notes = len(curr_notes)
        self.curr_notes = curr_notes 

    def __repr__(self):
        return "{} simultaneous notes: {}\n".format(
            self.num_simultaneous_notes, self.curr_notes)


class Note:

    def __init__(self, note_number, start, end, velocity):
        self.note_number = note_number
        self.octave = note_number_to_octave(note_number)
        self.tone = note_number_to_tone(note_number, self.octave)
        self.start = start
        self.end = end
        self.duration = end - start
        self.velocity = velocity
        self.video_position = None
        self.neighboring_notes = []
    
    def get_num_sim_notes(self):
        return len(self.neighboring_notes) + 1

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
    max_velocity = 0
    for event in miditrack:
        if _is_note_start(event):
            curr_events.append(event)
        elif _is_note_end(event):
            for i in range(len(curr_events)):
                ev = curr_events[i]
                p = _event_pitch(ev)
                if _event_pitch(ev) == _event_pitch(event):
                    vel = ev.get_velocity()
                    note = Note(p, ev.tick, event.tick, vel)
                    max_velocity = max(vel, max_velocity)
                    parsed_notes.append(note)
                    curr_events.remove(ev)
                    break
    _parse_events(parsed_notes)
    return parsed_notes, max_velocity


def _parse_events(parsed_notes):
    """
    Assigns the neighboring_notes lists to each note
    as well as their video positions.
    """
    note_starts = {}
    note_ends = {}

    # create dictionaries containing information on when
    # the notes start and end
    for note in parsed_notes:
        start = note.start
        if not start in note_starts:
            note_starts[start] = []
        note_starts[start].append(note)

        end = note.end
        if not end in note_ends:
            note_ends[end] = []
        note_ends[end].append(note)

    event_times = sorted(note_starts.keys() + note_ends.keys())
    total_events = {}
    curr_sim_notes = 0
    max_sim_notes = 0
    curr_notes = []

    # create track events containing which
    # notes are playing at a particular instance
    for time in event_times:
        if time in note_starts:
            curr_notes = _list_union(curr_notes, note_starts[time])
        if time in note_ends:
            curr_notes = _list_subtract(curr_notes, note_ends[time])
        max_simultaneous_notes = max(max_sim_notes, len(curr_notes))
        total_events[time] = TrackEvent(time, curr_notes)

    # for each of the notes in the list of parsed notes, put
    # fill their neighboring notes lists.
    for note in parsed_notes:
        start = note.start
        end = note.end
        this_note_number = note.note_number
        related_events = _find_events_between_inclusive(start, end,
                                                        event_times,
                                                        total_events)
        for event in related_events:
            for n in event.curr_notes:
                if n.note_number != this_note_number:
                    note.neighboring_notes.append(n)
    
    # finally, assign the video positions
    for note in parsed_notes:
        if note.video_position is None:
            note_nums = sorted([n.note_number for n in 
                                note.neighboring_notes] + [note.note_number])
            note.video_position = note_nums.index(note.note_number)

    # 1. Go through each parsed note again.
    # 2. Use the list of sorted event_times to find ALL events between
    #    the note's start and end.
    # 3. Store num_sim_notes in this note as the highest of the events
    #    you collected.
    # 4. Add all curr_notes from these events into a list of neighboring
    #    notes in the note object.(maybe?)
    # 5. Unless already done so, assign video positions to all these notes.
    # 6. We no longer need to return the events.


def _find_events_between_inclusive(start, end, sorted_times, total_events):
    first_index = _find_index_sorted(start, sorted_times)
    last_index = _find_index_sorted(end, sorted_times)
    times = sorted_times[first_index:last_index+1]
    return [total_events[t] for t in times]


def _find_index_sorted(el, sorted_list):
    """
    Performs binary search to find the index of the
    given element in a sorted list.
    """
    first = 0
    last = len(sorted_list)
    while True:
        i = (first + last)//2
        if sorted_list[i] == el:
            return i
        elif sorted_list[i] > el:
            last = i - 1
        else:
            first = i + 1


def _list_subtract(l1, l2):
    """
    Returns a list with all elements in l1 that
    aren't in l2.
    """
    return list(filter(lambda x: x not in l2, l1))


def _list_union(l1, l2):
    """
    Returns the union of l1 and l2
    """
    res = []
    for x in l1 + l2:
        if x not in res:
            res.append(x)
    return res


# def _add_note_to_parsed_events(parsed_events, note):
#     start = note.start
#     end = note.end
#     num_simultaneous_notes = 1
#     if start not in parsed_events:
#         parsed_events[start] = TrackEvent(start, 1)
#         parsed_events[start].started_notes.append(note)
#     else:
#         parsed_events[start].started_notes.append(note)
#         parsed_events[start].num_simultaneous_notes += 1
#         num_simultaneous_notes = parsed_events[start].num_simultaneous_notes
#     if end not in parsed_events:
#         parsed_events[end] = TrackEvent(end, 1)
#         parsed_events[end].ended_notes.append(note)
#     else:
#         parsed_events[end].ended_notes.append(note)
#         parsed_events[end].num_simultaneous_notes += 1
#         num_simultaneous_notes = parsed_events[end].num_simultaneous_notes
#     note.video_position = num_simultaneous_notes - 1
#     return num_simultaneous_notes


def note_number_to_octave(note_number):
    return note_number // len(TONES)


def note_number_to_tone(note_number, octave):
    return TONES[note_number - octave * len(TONES)]


def note_number_to_note_string(note_number):
    octave = note_number_to_octave(note_number)
    tone = note_number_to_tone(note_number, octave)
    return tone + str(octave)


def get_tempo(midipattern):
    """Returns the tempo of the song in bpm"""
    for p in midipattern[0]:
        if isinstance(p, midi.SetTempoEvent):
            return p.get_bpm()

    return DEFAULT_TEMPO


def get_resolution(midipattern):
    return midipattern.resolution


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

