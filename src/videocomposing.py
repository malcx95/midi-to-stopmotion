import multiprocessing
import vidpy
import moviepy.editor as edit
import pdb
import midiparse
import random
import os
import audioanalysis
import math
import json
import time
import progress.bar as bar
import sys
import traceback

# Message: (1, 0)
MSG_PROCESSED_SEGMENT = 1

# Message: (2, Exception)
MSG_FATAL_ERROR = 2

# Message: (3, num processed segments)
MSG_DONE = 3

SUPPORTED_EXTENSIONS = ['mp4']
WORKING_DIR_NAME = 'temp'
OFFSET_FILE_NAME = 'offset.json'

MIN_NUM_MEASURES_BEFORE_SPLIT = 2

MAX_NUM_SIM_TRACKS = 9


def compose(instruments, midipattern, width, 
            height, source_dir, volume_file_name,
            num_threads, instrument_config_file):
    _create_working_dir()
    volumes = _try_load_json_file(volume_file_name)
    instrument_config = _try_load_json_file(instrument_config_file)
    tempo = midiparse.get_tempo(midipattern)
    resolution = midiparse.get_resolution(midipattern)
    pulse_length = 60.0/(tempo*resolution)

    # analysed_tracks :: {(name1, name2, ...): (notes, max_velocity)}
    analysed_tracks = _analyse_all_tracks(midipattern, resolution)

    track_clip_file_names = []
    total_num_tracks = len(analysed_tracks)
    processes = []
    for instrument_names, (notes, max_velocity) in analysed_tracks.items():
        
        file_name = os.path.join(WORKING_DIR_NAME, '-'.join(instrument_names)
                                 + '.mp4')
        track_clip_file_names.append((len(notes), file_name))
        queue = multiprocessing.Queue()
        args = (instruments, instrument_names, source_dir, instrument_config,
                notes, pulse_length, width, height, max_velocity,
                queue, file_name, volumes, total_num_tracks)
        process = multiprocessing.Process(target=_process_track, args=args)
        processes.append((instrument_names, process, queue))

    running_processes = []

    progress_bar = bar.ChargingBar('', max=total_num_tracks)
    done = False
    num_processed_tracks = 0
    while not done:
        time.sleep(0.1)
        done_instruments = []
        for instrument_names, process, queue in running_processes:
            while not queue.empty():
                msg_type, contents = queue.get()
                if msg_type == MSG_PROCESSED_SEGMENT:
                    num_processed_tracks += 1
                    progress_bar.next()
                elif msg_type == MSG_DONE:
                    done_instruments.append(instrument_names)
                elif msg_type == MSG_FATAL_ERROR:
                    raise contents

        processes_changed = False

        # remove the instruments that are done
        for instrument_names in done_instruments:
            index = 0
            for i, (i_name, p, q) in enumerate(running_processes):
                if instrument_names == i_name:
                    index = i
                    break
            _, process, queue = running_processes.pop(index)
            process.join()
            processes_changed = True

        while len(running_processes) < num_threads and len(processes) > 0:
            p = processes.pop()
            p[1].start()
            running_processes.append(p)
            processes_changed = True

        if not running_processes:
            done = True

        if processes_changed and not done:
            progress_message = "Processing instruments: "
            for names, _, _ in running_processes:
                progress_message += '(' + ', '.join(names) + ')' + ', '
            progress_message = '\n' + progress_message[:-2]
            print(progress_message)
    
    progress_bar.finish()

    track_clip_file_names.sort(key=lambda k: k[0], reverse=True)

    final_clips = []
    for i, (_, file_name) in enumerate(track_clip_file_names):
        clip = vidpy.Clip(file_name)
        x, y, w, h = _partition(width, height, len(track_clip_file_names), i)
        clip.position(x = x, y = y, w = w, h = h)
        final_clips.append(clip)
    return vidpy.Composition(clips=final_clips, width = width, height = height)


def _create_working_dir():
    if not os.path.isdir(WORKING_DIR_NAME):
        os.makedirs(WORKING_DIR_NAME)


def _try_load_json_file(json_file_name):
    if json_file_name is None:
        return None
    with open(json_file_name) as f:
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


def _num_overlapping_notes(track1, track2):
    """
    Returns the number of notes in the given tracks that overlap.
    The given lists of tracks must be sorted by start time.
    """
    res = 0
    for n1 in track1:
        for n2 in track2:
            if n2.start > n1.end:
                break
            elif n1.start == n2.start or n1.end == n2.end:
                res += 1
            elif n1.start < n2.start:
                if n1.end > n2.start:
                    res += 1
            elif n1.end > n2.end:
                if n1.start < n2.end:
                    res += 1

    return res


def _merge_tracks_with_min_overlap(analysed_tracks):
    """
    Merges the two least overlapping tracks 
    """
    pairs = []
    for name1 in analysed_tracks:
        for name2 in analysed_tracks:
            track1, _ = analysed_tracks[name1]
            track2, _ = analysed_tracks[name2]
            overlap = _num_overlapping_notes(track1, track2)
            pairs.append((name1, name2, overlap))
    name1, name2, overlap = min(pairs, key=lambda k: k[2])
    track1, max_velocity1 = analysed_tracks[name1]
    track2, max_velocity2 = analysed_tracks[name2]
    del analysed_tracks[name1]
    del analysed_tracks[name2]
    analysed_tracks[name1 + name2] = (sorted(track1 + track2, 
                                             key=lambda n: n.start), 
                                      max(max_velocity1, max_velocity2))

    


def _merge_analysed_tracks(analysed_tracks):
    """
    Merges the tracks of analysed_tracks that don't overlap with eachother.
    """
    while len(analysed_tracks.keys()) > MAX_NUM_SIM_TRACKS:
        _merge_tracks_with_min_overlap(analysed_tracks)


def _analyse_all_tracks(midipattern, resolution):
    total_num_ticks = midiparse.get_total_num_ticks(midipattern)
    analysed_tracks = {(midiparse.get_instrument_name(miditrack),): 
                       midiparse.analyse_track(miditrack, total_num_ticks)
                       for miditrack in filter(midiparse.has_notes,
                                               midipattern)}
    _merge_analysed_tracks(analysed_tracks)
    for track, _ in analysed_tracks.values():
        midiparse.assign_video_positions(track)
        
    return analysed_tracks


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


def _load_instrument_clips(instrument_name, instrument_notes, 
                           source_dir, instrument_config):
    res = {}
    instrument_path = None
    if instrument_config is not None:
        instrument_path = instrument_config[instrument_name]
    else:
        instrument_path = os.path.join(source_dir, instrument_name)

    min_vol = float('inf')
    avail_tones = _get_available_tones(instrument_path)
    mapped_notes = _map_notes(avail_tones, instrument_notes)

    while True:
        try:
            offset_map = _try_load_offset_file(instrument_path)
            break
        except IOError:
            time.sleep(1)
        

    edited_offset_map = False

    for note_number, note_str in mapped_notes.items():
        # note_str = midiparse.note_number_to_note_string(note_number)

        file_name = os.path.join(instrument_path, 
                                 note_str + ".mp4")

        clip = edit.VideoFileClip(file_name)
        tmp_file = os.path.join(WORKING_DIR_NAME,
                                'STUPIDMOVIEPY' + note_str + instrument_name + '.mp4')

        offset, max_vol = None, None
        if offset_map is not None and note_number in offset_map:
            offset, max_vol = offset_map[note_number]
        else:
            offset, max_vol = audioanalysis.find_offset_and_max_vol(clip)
            clip.write_videofile(tmp_file, progress_bar=False, verbose=False)
            offset_map[note_number] = (offset, max_vol)
            edited_offset_map = True
            os.remove(tmp_file)

        res[note_number] = (vidpy.Clip(file_name), offset, max_vol)
        min_vol = min(min_vol, max_vol)

    if edited_offset_map:
        _write_offset_file(instrument_path, offset_map)

    return res, min_vol


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


def _process_track(instruments, instrument_names, source_dir, 
                   instrument_config,
                   notes, pulse_length,
                   width, height, max_velocity, 
                   queue, file_name, volumes, num_sim_tracks):
    """
    Composes one midi track into a stop motion video clip.
    Writes a file of this with the given file name.
    """
    try:
        instrument_clips = {name: _load_instrument_clips(name, 
                                                         instruments[name],
                                                         source_dir,
                                                         instrument_config)
                           for name in instrument_names}
        parsed_clips = []
        scale_factor = int(math.floor(math.log(num_sim_tracks, 2) + 1))
        if os.path.isfile(file_name):
            queue.put((MSG_PROCESSED_SEGMENT, 0))
            queue.put((MSG_DONE, 1))
            return
        for note in notes:
            note_number = note.note_number
            clips, min_vol = instrument_clips[note.instrument_name]
            vol = 0.5
            if volumes is not None:
                vol = volumes.get(note.instrument_name, 0.5)

            c, offset, max_vol = clips[note_number]
            clip = vidpy.Clip(c.resource)
            num_sim_notes = note.get_num_sim_notes()

            x, y, w, h = _partition(width, height, 
                                    num_sim_notes, note.video_position)

            volume = (float(note.velocity)/float(max_velocity))*(min_vol/max_vol)

            clip.cut(start=offset)
            clip.set_offset((note.start)*pulse_length)
            clip.volume(volume*vol)
            d = clip.duration
            clip.set_duration(min(note.duration*pulse_length, d))
            clip.position(
                x = x//scale_factor, y = y//scale_factor,
                w = w//scale_factor, h = h//scale_factor
            )
            parsed_clips.append(clip)
        track_clip = vidpy.Composition(clips=parsed_clips, width=width//scale_factor, height=height//scale_factor)
        track_clip.save(file_name)

        queue.put((MSG_PROCESSED_SEGMENT, 0))
        queue.put((MSG_DONE, 1))

    except Exception as e:
        queue.put((MSG_FATAL_ERROR, e))
        traceback.print_exc(file=sys.stdout)

