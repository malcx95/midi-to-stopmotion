# Create stop motion video from a MIDI-file

This script takes in a MIDI-file, and footage of you playing instruments,
and composes it to a stop motion video, kind of like MysteryGuitarMan did
manually back in 2010. An example of the output when the input was a MIDI
file of Through the Fire and Flames by DragonForce can be found below:

[![Through the Fire and Cringe - Automatic stop-motion video](http://img.youtube.com/vi/LJeUr76gGnc/0.jpg)](https://www.youtube.com/watch?v=LJeUr76gGnc)

## Running the script

Firstly, install all dependencies, which include `python2`, [python-midi](https://github.com/vishnubob/python-midi), [moviepy](https://zulko.github.io/moviepy/install.html) and [progress](https://pypi.org/project/progress/).

When using a new midi file, you first need to find out which instruments are played. This can be done with:

```
python2 main.py -m my_midi_file.mid -i
```

This will print a list of instruments and which notes are played. Then, you need to record videos of each played note.
You need to make a video for each note that was printed in the command for each instrument.
It's fine, however, if you only record A2 when the song used both A2 and A3, but the program will then use A2 for both.
In each video, play only one note, and make sure the loudest sound in that video was the note itself, as the script
automatically finds the start of each note. Title the video exactly with the note that was played. For instance, if
the script when running the `-i` command printed this:

```
Instrument 'Guitar' plays these tones:
F3
G3
A#2
A4

Instrument 'Piano' plays these tones:
F4
G4
A2
```

then you should create a file system of the following structure:

```
instruments/
    Guitar/
        F3.mp4
        G3.mp4
        A#2.mp4
        A4.mp4
    Piano/
        F4.mp4
        G4.mp4
        A2.mp4
```

Optionally, you might want to use the same recordings for different instruments. In that case, create a `json` file,
where you map each instrument name to the path to the instruments you want to be used:

```json
{
    "Lead 1": "../instruments/marieguitar",
    "Acoustic Guitar": "../instruments/marieguitar",
    "Backing Vocals": "../instruments/voice",
    "Guitar 1 ": "../instruments/guitar",
    "Drums": "../ttfafdrums",
    "Lead 2": "../instruments/guitar",
    "Acoustic+Keyboard": "../instruments/bass",
    "Keyboard": "../instruments/voice",
    "Vocals": "../instruments/marieguitar",
    "Guitar 2": "../instruments/marieguitar",
    "Ensemble": "../instruments/voice",
    "Bass": "../instruments/bass"
}
```

If you want to use this config, supply it with the `-c` flag to the script, otherwise use the `-s` flag to specify 
the path to all instruments.

You might also want to tweak the volume of each instrument. For this purpose, use another `json` file where each
instrument is mapped to the volume it should have:

```
{
    "Vocals": 1.3,
    "Lead 1": 1.1,
    "Lead 2": 0.8,
    "Drums": 0.3,
    "Guitar 1 ": 0.3,
    "Guitar 2": 0.7,
    "Bass": 0.5,
    "Backing Vocals": 0.7,
    "Keyboard": 1.0,
    "Ensemble": 0.6
}
```

Supply the `json` file with the `-v` command to use it.

