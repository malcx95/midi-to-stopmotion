import moviepy.editor as edit
import moviepy.video.fx.all as fx
import pdb
import midiparse
import random
import os
import audioanalysis


def compose(instruments, midipattern, width, height, source_dir):
    tempo = midiparse.get_tempo(midipattern)
    resolution = midiparse.get_resolution(midipattern)
    pulse_length = 60/(tempo*resolution)
    # pdb.set_trace()
    written_clips = []
    for i, track in enumerate(midipattern[1:]):
        print "Composing track " + str(i) + "..."
        name = midiparse.get_instrument_name(track)
        file_name = name + '.mp4'
        if os.path.isfile(file_name):
            written_clips.append((len(track), file_name))
            continue
        if name is None:
            # FIXME this is ugly
            name = "Untitled Instrument 1"
        instrument_clips = _load_instrument_clips(name, 
                                                  instruments[name],
                                                  source_dir)
        try:
            track_clip = _process_track(instrument_clips,
                                          track, pulse_length, width, height)
            track_clip.write_videofile(file_name)
            written_clips.append((len(track), file_name))
            _delete_clips(instrument_clips)
            del instrument_clips
        except IOError:
            raise
        except Exception as e:
            print "Couldn't process instrument {}: {}, continuing...".format(
                name, e.message)
            continue

    written_clips.sort(key=lambda s: s[0], reverse=True)

    final_clips = []
    for i, (_, file_name) in enumerate(written_clips):
        clip = edit.VideoFileClip(file_name)
        x, y, w, h = _partition(width, height, len(written_clips), i)
        final_clips.append(
            fx.resize(clip, newsize=(w, h)).set_position((x, y)))
    return edit.CompositeVideoClip(size=(width, height), clips=final_clips)


def _load_instrument_clips(instrument_name, instrument_notes, source_dir):
    res = {}
    for note_number in instrument_notes:
        note_str = midiparse.note_number_to_note_string(note_number)
        file_name = ""
        file_name = os.path.join(source_dir, instrument_name,
                                     note_str + ".mp4")
        if not os.path.isfile(file_name):
            error("The required file \"{}\" couldn't be found"
                  .format(file_name))

        res[note_number] = edit.VideoFileClip(file_name)
    return res

def _delete_clips(instrument_clips):
    keys = instrument_clips.keys()
    for key in keys:
        del instrument_clips[key]


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
    if num_sim_notes <= 4:
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
    else:
        w = width//3
        h = height//3
        if pos > 10:
            # place it off screen
            return width, height, w, h
        return (pos // 3)*w, (pos % 3)*h, w, h




def _process_track(clips, midi_track, pulse_length, width, height):
    """
    Composes one midi track into a stop motion video clip.
    Returns a CompositeVideoClip.
    """
    parsed_clips = []
    parsed_notes, parsed_events, max_simultaneous_notes, max_velocity = \
            midiparse.analyse_track(midi_track)
    for note in parsed_notes:
        note_number = note.note_number
        clip = clips[note_number].copy()
        curr_event = parsed_events[note.start]
        num_sim_notes = curr_event.num_simultaneous_notes
        x, y, w, h = _partition(width, height, 
                                num_sim_notes, note.video_position)
        #if note.duration*pulse_length*2 < audioanalysis.STANDARD_OFFSET:
        volume = float(note.velocity) / float(max_velocity)

        clip = clip.subclip(audioanalysis.STANDARD_OFFSET)
        clip = clip.set_start(note.start*pulse_length)
        clip = clip.volumex(volume)
        d = clip.duration
        clip = clip.set_duration(min(note.duration*pulse_length*2, d))
        clip = clip.set_position((x, y))
        clip = fx.resize(clip, newsize=(w, h))
        parsed_clips.append(clip)
    return edit.CompositeVideoClip(size=(width, height), clips=parsed_clips)

