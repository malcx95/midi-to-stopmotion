import moviepy.editor as edit
import moviepy.video.fx.all as fx
#import moviepy.video as video
import pdb
import midiparse
import random


def compose(instrument_clips, midipattern, width, height):
    tempo = midiparse.get_tempo(midipattern)
    resolution = midiparse.get_resolution(midipattern)
    pulse_length = 60/(tempo*resolution)
    track_clips = []
    for track in midipattern[1:]:
        name = midiparse.get_instrument_name(track)
        if name is None:
            # FIXME this is ugly
            name = "Untitled Instrument 1"
        track_clips.append(_process_track(instrument_clips[name],
                                          track, pulse_length, width, height))
    if len(track_clips) == 1:
        return track_clips[0]
    else:
        final_clips = []
        for i, clip in enumerate(track_clips):
            x, y, w, h = _partition(width, height, len(track_clips), i)
            final_clips.append(
                fx.resize(clip, newsize=(w, h)).set_position(x, y))
        return edit.CompositeVideoClip(size=(width, height), clips=final_clips)


def _partition(width, height, num_sim_notes, pos):
    """
    Returns a position and size a clip should
    have when it shares space with other clips, the number of
    which is given by num_sim_notes. The number pos indicates which
    exact position this particular clip should get (0:th, 1:st...)

    Please don't look too much at this spaghetti-code.
    """
    if num_sim_notes == 1:
        return 0, 0, width, height
    w = width//2
    h = height//2
    if pos < 4:
        # put it in one of 4 spots
        x = (pos // 2)*w
        y = (pos % 2)*h

        if num_sim_notes < 2:
            # if there are only two notes, vertically center
            # the clips 
            y += h
        elif num_sim_notes == 3 and pos == 2:
            # if there are a total of 3 clips, horizontally
            # center the last clip
            x += w
        return x, y, w, h
    else:
        # if there are more than 4, place it randomly on top of the others
        rx = random.randint(-w//2, w//2) + w
        ry = random.randint(-h//2, h//2) + h
        return rx, ry, w, h


def _process_track(clips, midi_track, pulse_length, width, height):
    """
    Composes one midi track into a stop motion video clip.
    Returns a CompositeVideoClip.
    """
    parsed_clips = []
    parsed_notes, parsed_events, max_simultaneous_notes = \
            midiparse.analyse_track(midi_track)
    for note in parsed_notes:
        note_number = note.note_number
        clip = clips[note_number].copy()
        curr_event = parsed_events[note.start]
        num_sim_notes = curr_event.num_simultaneous_notes
        x, y, w, h = _partition(width, height, 
                                num_sim_notes, note.video_position)
        clip = clip.set_start(note.start*pulse_length)
        d = clip.duration
        clip = clip.set_duration(min(note.duration*pulse_length, d))
        clip = clip.set_position((x, y))
        clip = fx.resize(clip, newsize=(w, h))
        parsed_clips.append(clip)
    return edit.CompositeVideoClip(size=(width, height), clips=parsed_clips)

