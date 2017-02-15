import midi


def get_instruments(midipattern):
    """
    Gets the a dictionary of the used instruments (tracks) in a midi pattern,
    mapped to the sorted list of unique note numbers that instrument plays.
    """
    result = {}
    i = 0
    for track in midipattern[1:]:
        i += 1
        name = _get_instrument_name(track, i)
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


def _get_instrument_name(miditrack, number):
    """
    Gets the instrument name (track name) of the midi track.
    """
    for event in miditrack:
        if isinstance(event, midi.TrackNameEvent):
            return event.text
    return "Untitled Instrument " + str(number)


def get_song_name(midipattern):
    """
    Gets the song name in the midi pattern.
    Returns None if no name was found.
    """
    for p in midipattern[0]:
        if isinstance(p, midi.TrackNameEvent):
            return p.text
    return None

