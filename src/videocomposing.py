import moviepy.editor as edit
import moviepy.video.fx.all as fx
import pdb
import midiparse
import random
import os
import audioanalysis
import math
import json

SUPPORTED_EXTENSIONS = ['mp4']
WORKING_DIR_NAME = 'temp'
OFFSET_FILE_NAME = 'offset.json'

MIN_NUM_MEASURES_BEFORE_SPLIT = 2


# TODO when composing all tracks, save an array where
# each index tells whether there is something playing
# at this timestamp. That way you can tell which clips
# should be shown and how to partition them

# Better idea: when parsing the midifile, 
# save all timestamps where there are no notes
# playing or when all the notes that were playing have stopped,
# so the track can be safely split at that point. Then,
# using this information about all tracks, find the timestamps
# where all tracks can be safely split. Then, for each of these timestamps,
# partition the song between these timestamps and compose them individually.
# Then when all tracks have been composed for one partition, compose these
# into one clip using _partition. Then finally, join all partitions into one
# clip.

# You might need to define a minimum length of a partition though, since,
# for instance, moments of complete silence would register as a whole lot
# of partitions. A minimum length of a one or two measures should be fine.

# Also multithread this, such that each thread processes a partition.


def compose(instruments, midipattern, width, 
            height, source_dir, volume_file_name):
    _create_working_dir()
    volumes = _try_load_volume_file(volume_file_name)
    tempo = midiparse.get_tempo(midipattern)
    resolution = midiparse.get_resolution(midipattern)
    pulse_length = 60.0/(tempo*resolution)

    # instrument_segments   :: {instrument name: (max_velocity, {(start, end): [notes]})}
    # song_segments         :: [((start, end), [(instrument name, segment file name)])]
    
    instrument_segments, song_segments = _analyse_all_tracks(
                                            midipattern, resolution)

    for instrument_name, (max_velocity, segments) in instrument_segments.items():
        print "Composing track " + instrument_name + "..."
        # if os.path.isfile(file_name):
        #     written_clips.append((len(parsed_notes), file_name, name))
        #     continue
        # if name is None:
        #     # FIXME this is ugly
        #     name = "Untitled Instrument 1"

        _process_track(instruments, instrument_name, source_dir,
                       segments, pulse_length, width, height,
                       max_velocity)
        # written_clips.append((len(parsed_notes), file_name, name))
        print ''
        # except Exception:
        #     raise
        # except IOError:
        #     raise
        # except Exception as e:
        #     print "Couldn't process instrument {}: {}, continuing...".format(
        #         name, e.message)
        #     continue

    # written_clips.sort(key=lambda s: s[0], reverse=True)

    final_clips = []
    for (start, end), simultaneous_segments in song_segments:
        segment_clips = []
        num_sim_segments = len(simultaneous_segments)
        for i, (instrument_name, segment_file) in enumerate(simultaneous_segments):
            vol = 0.5
            if volumes is not None:
                vol = volumes.get(instrument_name, 0.5)
            x, y, w, h = _partition(width, height, num_sim_segments, i)
            clip = edit.VideoFileClip(os.path.join(WORKING_DIR_NAME, 
                                                   segment_file))
            segment_clips.append(fx.resize(clip, newsize=(w, h))
                                 .set_position((x, y))
                                 .volumex(vol))

        comp_clip = edit.CompositeVideoClip(size=(width, height), 
                                            clips=segment_clips)
        final_clips.append(comp_clip.set_start(start*pulse_length))

    # for i, (_, file_name, instrument_name) in enumerate(written_clips):
    #     vol = 0.5
    #     if volumes is not None:
    #         vol = volumes.get(instrument_name, 0.5)
    #     clip = edit.VideoFileClip(file_name)
    #     x, y, w, h = _partition(width, height, len(written_clips), i)
    #     final_clips.append(
    #         fx.resize(clip, newsize=(w, h))
    #         .set_position((x, y))
    #         .volumex(vol)
    #     )
    return edit.CompositeVideoClip(size=(width, height), clips=final_clips)


def _create_working_dir():
    if not os.path.isdir(WORKING_DIR_NAME):
        os.makedirs(WORKING_DIR_NAME)


# def find_common_split_points(split_point_lists, min_duration):
#     res = []
#     first_list = split_point_lists[0]
# 
#     for time in first_list:
#         found = True
#         for l in split_point_lists[1:]:
#             if time not in l:
#                 found = False
#                 break
#         if found:
#             res.append(time)
#     
#     i = 0
#     while True:
#         if i + 1 >= len(res):
#             break
#         while res[i + 1] - res[i] < min_duration and i + 1 < len(res):
#             del res[i + 1]
# 
#     return res


def _try_load_volume_file(volume_file_name):
    if volume_file_name is None:
        return None
    with open(volume_file_name) as f:
        return json.loads(f.read())


def _get_common_split_points(all_split_points, resolution):
    common_split_points = []
    if len(all_split_points) == 1:
        common_split_points = list(all_split_points[0])
    else:
        first_split_points = all_split_points[0]
        for point in first_split_points:
            found = True
            for split_points in all_split_points:
                if point not in split_points:
                    found = False
                    break
            if found:
                common_split_points.append(point)

    min_num_ticks_to_split = resolution*MIN_NUM_MEASURES_BEFORE_SPLIT*4

    filtered_points = []
    last_split = float('-inf')

    for point in sorted(common_split_points):
        if point - last_split >= min_num_ticks_to_split:
            filtered_points.append(point)
            last_split = point

    return filtered_points


def _analyse_all_tracks(midipattern, resolution):
    total_num_ticks = midiparse.get_total_num_ticks(midipattern)
    analysed_tracks = {midiparse.get_instrument_name(miditrack): 
                       midiparse.analyse_track(miditrack, total_num_ticks)
                       for miditrack in filter(midiparse.has_notes,
                                               midipattern)}
    all_split_points = [analysis[2] for analysis in analysed_tracks.values()]

    split_tracks = _split_tracks(analysed_tracks,
                                 _get_common_split_points(all_split_points, 
                                                          resolution))
    instrument_segments = {}
    for range_, instrument_notes in split_tracks.items():
        for instrument_name, notes in instrument_notes.items():
            max_velocity = analysed_tracks[instrument_name][1]
            if instrument_name not in instrument_segments:
                instrument_segments[instrument_name] = (max_velocity, {})
            instrument_segments[instrument_name][1][range_] = notes

    song_segments = []
    for range_ in sorted(split_tracks.keys(), key=lambda r: r[0]):
        start, end = range_
        song_segments.append((range_, 
                              [(name, _segment_file_name(start, end, name))
                                  for name in split_tracks[range_]]))
    return instrument_segments, song_segments


def _segment_file_name(start, end, instrument):
    return '{}-{}-{}.mp4'.format(instrument, start, end)


def _extract_notes_between_ticks(start, end, analysed_tracks):
    res = {name: [] for name in analysed_tracks}

    for name, (parsed_notes, max_velocity, _) in analysed_tracks.items():
        for note in parsed_notes:
            if note.start >= end:
                break
            if note.start >= start and note.end <= end:
                res[name].append(note)
    
    # remove empty segments
    for name in res.keys():
        if not res[name]:
            del res[name]

    return res


def _split_tracks(analysed_tracks, split_points):
    result = {}
    
    # create ranges
    assert split_points[0] == 0
    start = split_points[0]
    for point in split_points[1:]:
        result[(start, point)] = None
        start = point

    for range_ in result.keys():
        start, end = range_
        result[range_] = _extract_notes_between_ticks(start, end,
                                                      analysed_tracks)
    return result
        

def _is_valid_tone_name(name):
    name_split = name.split('.')
    if len(name_split) != 2:
        return False
    tone, ext = name_split
    if ext not in SUPPORTED_EXTENSIONS:
        return False
    if '#' in tone and len(tone) == 3:
        return tone[:2] in midiparse.TONES and tone[-1].isdigit()
    elif len(tone) == 2:
        return tone[0] in midiparse.TONES and tone[-1].isdigit()


def _get_available_tones(source_dir):
    filenames = None
    for _, _, names in os.walk(source_dir):
        filenames = names
        break
    tones = [name.split('.')[0] for name in filenames
             if _is_valid_tone_name(name)]
    return tones


def _get_closest_note(avail_tones_split, target_note_number):
    target_octave = midiparse.note_number_to_octave(target_note_number)
    target_tone = midiparse.note_number_to_tone(target_note_number,
                                                target_octave)

    res_octave = None
    diff = float('inf')

    for tone, octave in avail_tones_split:
        if tone == target_tone and abs(octave - target_octave) < diff:
            res_octave = octave
            diff = abs(octave - target_octave)
    if res_octave is None:
        raise Exception('Required tone {} not found'.format(target_tone))

    return target_tone + str(res_octave)
            

def _map_notes(avail_tones, instrument_notes):
    res = {}
    avail_tones_split = [(tone[:-1], int(tone[-1])) for tone in avail_tones]
    for note in instrument_notes:
        note_str = midiparse.note_number_to_note_string(note)
        if note_str in avail_tones:
            res[note] = note_str
        else:
            res[note] = _get_closest_note(avail_tones_split, note)
    return res


def _try_load_offset_file(instrument_dir):
    file_name = os.path.join(instrument_dir, OFFSET_FILE_NAME)
    if os.path.isfile(file_name):
        with open(file_name) as f:
            offset_map = json.loads(f.read())
            return {int(k): v for k, v in offset_map.items()}
    return {}


def _write_offset_file(instrument_dir, offset):
    with open(os.path.join(instrument_dir, OFFSET_FILE_NAME), 'w') as f:
        f.write(json.dumps(offset))


def _load_instrument_clips(instrument_name, instrument_notes, source_dir):
    res = {}
    min_vol = float('inf')
    avail_tones = _get_available_tones(os.path.join(source_dir, 
                                                    instrument_name))
    mapped_notes = _map_notes(avail_tones, instrument_notes)
    offset_map = _try_load_offset_file(os.path.join(source_dir, 
                                                    instrument_name))
    edited_offset_map = False

    for note_number, note_str in mapped_notes.items():
        # note_str = midiparse.note_number_to_note_string(note_number)
        print "Loading " + note_str
        file_name = ""
        file_name = os.path.join(source_dir, instrument_name,
                                     note_str + ".mp4")

        clip = edit.VideoFileClip(file_name)
        tmp_file = os.path.join(WORKING_DIR_NAME,
                                'STUPIDMOVIEPY' + note_str + '.mp4')

        offset, max_vol = None, None
        if offset_map is not None and note_number in offset_map:
            offset, max_vol = offset_map[note_number]
        else:
            offset, max_vol = audioanalysis.find_offset_and_max_vol(clip)
            print 'Analysing ' + note_str + '...'
            clip.write_videofile(tmp_file, progress_bar=False, verbose=False)
            offset_map[note_number] = (offset, max_vol)
            edited_offset_map = True
            os.remove(tmp_file)

        res[note_number] = (clip, offset, max_vol)
        min_vol = min(min_vol, max_vol)

    if edited_offset_map:
        _write_offset_file(os.path.join(source_dir, instrument_name),
                           offset_map)

    return res, min_vol


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
            x = (pos % 2)*w
            y = (pos // 2)*h

            # if num_sim_notes < 2:
            #     # if there are only two notes, vertically center
            #     # the clips 
            #     y += h
            # elif num_sim_notes == 3 and pos == 2:
            #     # if there are a total of 3 clips, horizontally
            #     # center the last clip
            #     x += w
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


def _process_segment(segment, pulse_length, width, height, max_velocity,
                     file_name, clips, min_vol, segment_start):
    parsed_clips = []
    for note in segment:
        note_number = note.note_number
        c, offset, max_vol = clips[note_number]
        clip = c.copy()
        num_sim_notes = note.get_num_sim_notes()

        x, y, w, h = _partition(width, height, 
                                num_sim_notes, note.video_position)

        volume = (float(note.velocity)/float(max_velocity))*(min_vol/max_vol)

        clip = clip.subclip(offset)
        clip = clip.set_start((note.start - segment_start)*pulse_length)
        clip = clip.volumex(volume)
        d = clip.duration
        clip = clip.set_duration(min(note.duration*pulse_length, d))
        clip = clip.set_position((x, y))
        clip = fx.resize(clip, newsize=(w, h))
        parsed_clips.append(clip)
    track_clip = edit.CompositeVideoClip(size=(width, height), 
                                         clips=parsed_clips)
    track_clip.write_videofile(file_name, fps=24, 
                               verbose=False, progress_bar=False)


def _process_track(instruments, instrument_name, source_dir, 
                   segments, pulse_length,
                   width, height, max_velocity):
    """
    Composes one midi track into a stop motion video clip.
    Writes a file of this with the given file name.
    """
    clips, min_vol = _load_instrument_clips(instrument_name, 
                                            instruments[instrument_name],
                                            source_dir)
    parsed_clips = []
    # scale_factor = int(math.floor(math.log(num_sim_tracks, 2) + 1))
    for i, ((start, end), segment) in enumerate(segments.items()):
        file_name = os.path.join(WORKING_DIR_NAME, 
                                 _segment_file_name(start, end, 
                                                    instrument_name))
        print 'Processing segment {} out of {}, as file {}...'.format(
                i+1, len(segments), file_name)
        if os.path.isfile(file_name):
            continue
        _process_segment(segment, pulse_length, width, 
                         height, max_velocity, file_name, 
                         clips, min_vol, start)

