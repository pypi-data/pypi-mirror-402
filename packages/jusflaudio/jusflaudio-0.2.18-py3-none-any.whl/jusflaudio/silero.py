#!/usr/bin/env python3

from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
import click
import sys
from pydub import AudioSegment
import glob
import os

# ================================================================================
#
# --------------------------------------------------------------------------------

@click.command()
@click.argument('afile', default=None)
def main_silero(afile):
    if afile is None:
        print(f"")
        sys.exit(1)
    model = load_silero_vad()
    wav = read_audio(afile)
    speech_timestamps = get_speech_timestamps(
        wav,
        model,
        return_seconds=True,  # Return speech timestamps in seconds (default is samples)
    )
    print(speech_timestamps)
    return 0



@click.command()
@click.argument('input_file', default=None)
@click.option('--segment_length', default=15, help='Segment length in minutes')
def main_pydub(input_file, segment_length):
    if input_file is None:
        print(f"")
        sys.exit(1)

    audio = AudioSegment.from_file(input_file)
    segment_ms = segment_length * 60 * 1000
    base_name, ext = os.path.splitext(os.path.basename(input_file))
    for i, start in enumerate(range(0, len(audio), segment_ms)):
        outname = f"{base_name}_part{i+1}{ext}"
        print(i, outname )
        segment = audio[start:start+segment_ms]
        segment.export( outname , format=ext[1:])



@click.command()
@click.argument('input_file', default=None)
@click.option('--segment_length', default=15, help='Segment length in minutes')
def main(input_file, segment_length):
    if input_file is None:
        print(f"")
        sys.exit(1)

    pabase = os.path.splitext(input_file)[1]
    ext = os.path.splitext(input_file)[1]

    folder = pabase + "_chunks"
    print("i... ", folder)
    print("i... ", ext)
    pattern = os.path.join(folder, f"chunks_*{ext}")
    print("i... ", pattern)
    files = sorted(glob.glob(pattern))
    for f in files:
        print("i... ", os.path.basename(f))

    print("")
    print(f"""i... now you can run
 fawhis {folder} -w -m base.en

    """)



# ================================================================================
#
# ================================================================================

if __name__ == "__main__":
    main()
