#!/usr/bin/env python

import numpy as np
from scipy.fftpack import fft, fftfreq
import scipy
import moviepy.editor as edit
import matplotlib.pyplot as plt
import pdb
import scipy.signal as signal
import os
import argparse
from frequencies import FREQUENCIES

START_THRESHOLD = 0.02
END_THRESHOLD = 0.01
DOWNSAMPLE_FACTOR = 2
KERNEL_SIZE = 7000
STANDARD_OFFSET = 0.1

SAMPLE_FREQUENCY = 44100

AUDIO_START_THRESHOLD = 0.9


def analyse_instrument(video, output_name):
    clips = _split_clip(video)
    for i, clip in enumerate(clips):
        clip.write_videofile(output_name.split('.')[0] + str(i) + '.mp4')


def _remove_tmp_audio(file_name):
    os.remove(file_name)


def _extract_audio(video):
    audio = video.audio
    a = audio.to_soundarray()#fps=SAMPLE_FREQUENCY)
    return (a[:, 0] + a[:, 1])*0.5
    # return signal.decimate((a[:, 0] + a[:, 1])*0.5, DOWNSAMPLE_FACTOR)


def find_offset(clip):
    """
    Returns the amount of time in seconds before the note starts.
    """
    audio = _extract_audio(clip)
    
    clip_abs = np.abs(audio)
    threshold = np.max(clip_abs)*AUDIO_START_THRESHOLD
    tot_duration = clip.duration
    i = 0
    while i < len(clip_abs):
        if clip_abs[i] >= threshold:
            return float(i)*tot_duration/float(len(clip_abs))
        i += 1

    raise Exception("This should never happen")
    

def _split_clip(video):
    # pdb.set_trace()
    audio = _extract_audio(video)
    kernel = np.ones((KERNEL_SIZE,))/KERNEL_SIZE
    clip_abs = np.abs(audio)
    filtered = signal.convolve(clip_abs, kernel, mode='same')
    i = 0
    indices = []

    while i < len(filtered):
        if filtered[i] > START_THRESHOLD:
            start = i
            while i < len(filtered) and filtered[i] > END_THRESHOLD:
                i += 1
            end = i - 1
            indices.append((start, end))
        else:
            i += 1
    
    tot_duration = video.duration
    a_samples = float(len(filtered))
    return [video.subclip(tot_duration*float(start)/a_samples
                           - STANDARD_OFFSET,
                           tot_duration*float(end)/a_samples)
                          for start, end in indices]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', required=True, 
                        help='The input video')
    parser.add_argument('-o', '--out', default='out',
                       help='The output file name')
    args = parser.parse_args()
    video = edit.VideoFileClip(args.source)
    clips = analyse_instrument(video, args.out)


if __name__ == "__main__":
    main()
