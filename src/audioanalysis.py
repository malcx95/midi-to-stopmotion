import numpy as np
from scipy.fftpack import fft
import scipy
import moviepy.editor as edit
import matplotlib.pyplot as plt
import pdb
import scipy.signal as signal
import os

START_THRESHOLD = 0.02
END_THRESHOLD = 0.01
DOWNSAMPLE_FACTOR = 2
KERNEL_SIZE = 7000
STANDARD_OFFSET = 0.1

def analyse_instrument(video):
    clips = _split_clip(video)
    for i, clip in enumerate(clips):
        print clip.duration
        clip.write_videofile('testdir/test' + str(i) + '.mp4')
    

def _remove_tmp_audio(file_name):
    os.remove(file_name)


def _extract_audio(video):
    audio = video.audio
    a = audio.to_soundarray(buffersize=20000)
    return signal.decimate((a[:, 0] + a[:, 1])*0.5, DOWNSAMPLE_FACTOR)
    

def _split_clip(video):
    # pdb.set_trace()
    audio = _extract_audio(video)
    kernel = np.ones((KERNEL_SIZE,))/KERNEL_SIZE
    clip_abs = np.abs(audio)
    filtered = signal.convolve(clip_abs, kernel, mode='same')
    i = 0
    indices = []

    # TODO record with more silence between notes

    while i < len(filtered):
        if filtered[i] > START_THRESHOLD:
            start = i
            while i < len(filtered) and filtered[i] > END_THRESHOLD:
                i += 1
            end = i - 1
            indices.append((float(start)/float(len(filtered)),
                            float(end)/float(len(filtered))))
        else:
            i += 1
    
    tot_duration = video.duration
    clips = []
    for start, end in indices:
        clips.append(video.subclip(start*tot_duration - STANDARD_OFFSET,
                                   end*tot_duration))
    return clips

    
    # plt.figure(1)
    # plt.subplot(2, 1, 1)
    # plt.plot(clip_abs)
    # plt.subplot(2, 1, 2)
    # plt.plot(filtered)
    # plt.show()


def main():
    video = edit.VideoFileClip('../test-auto/testvideo.mp4')
    clips = analyse_instrument(video)


if __name__ == "__main__":
    main()
