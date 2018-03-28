import pdb
import midi

TONES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

DEFAULT_TEMPO = 96

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
        self.num_sim_notes = 0
        # self.neighboring_notes = []
    
    def get_num_sim_notes(self):
        # return len(self.neighboring_notes) + 1
        return self.num_sim_notes

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


def has_notes(miditrack):
    if not miditrack:
        return False
    for event in miditrack:
        if isinstance(event, midi.NoteOnEvent):
            return True
    return False


def get_total_num_ticks(midipattern):
    max_ticks = 0
    for track in filter(has_notes, midipattern):
        max_ticks = max(max_ticks, track[-1].tick)
    return max_ticks


def analyse_track(miditrack, total_num_ticks):
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
    split_points = _parse_events(parsed_notes, total_num_ticks)
    return parsed_notes, max_velocity, split_points


def _parse_events(parsed_notes, total_num_ticks):
    """
    Assigns the neighboring_notes lists to each note
    as well as their video positions. Also returns
    a list of timestamps where it's safe to split
    the song.
    """
    note_starts = {}
    note_ends = {}
    split_points = set()

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
            # started_notes = note_starts[time]
        if time in note_ends:
            curr_notes = _list_subtract(curr_notes, note_ends[time])

        # safe to split here
        # if not curr_notes or _note_lists_equal(curr_notes, note_starts[time]):
        #     split_points.append(time)

        # curr_notes = _list_union(curr_notes, started_notes)
        max_simultaneous_notes = max(max_sim_notes, len(curr_notes))
        total_events[time] = TrackEvent(time, curr_notes)

    # pdb.set_trace()

    # for each of the notes in the list of parsed notes, put
    # fill their neighboring notes lists.
    for time, notes in note_starts.items():
        for i, n in enumerate(notes):
            n.video_position = i
            n.num_sim_notes = len(notes)

    time = 0
    curr_num_notes = 0

    while time < total_num_ticks:
        event = total_events.get(time, None)
        if event is None and curr_num_notes == 0:
            split_points.add(time)
        elif event is not None:
            curr_num_notes = event.num_simultaneous_notes
            if curr_num_notes == 0:
                split_points.add(time)
        time += 1

    # for note in parsed_notes:
    #     start = note.start
    #     end = note.end
    #     this_note_number = note.note_number
    #     
    #     # related_events = note_starts[start]
    #     related_events = _find_events_between_inclusive(start, end,
    #                                                     event_times,
    #                                                     total_events)
    #     for event in filter(lambda e: e not in parsed_events, related_events):
    #         for n in event.curr_notes:
    #             if n.note_number != this_note_number:
    #                 note.neighboring_notes.append(n)
    #         parsed_events.add(event)
    # 
    # # finally, assign the video positions
    # for note in parsed_notes:
    #     if note.video_position is None:
    #         note_nums = sorted([n.note_number for n in 
    #                             note.neighboring_notes] + [note.note_number])
    #         note.video_position = note_nums.index(note.note_number)
    return split_points


def _note_lists_equal(l1, l2):
    if len(l1) != len(l2):
        return False
    numbers = set(n.note_number for n in l1)
    for n in l2:
        if n.note_number in numbers:
            return True
    return False



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
    for track in filter(has_notes, midipattern):
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

