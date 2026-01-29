#!/usr/bin/env python3
import click
import sys
import shlex
import subprocess as sp
from console import  fg, bg

import os
import glob

import srt
import re
import datetime as dt
#  like mpv but try to get audio and subtitle based on similarity
#  also creates spectrogram
#
#
#

from jusflaudio.check_new_version import is_there_new_version
from jusflaudio.whisper_wrapper import create_english_whisper, create_multilingual_whisper, check_dependencies
from jusflaudio.tool_checker import verify_model_availability

# Create and configure logger for mpvsa
import logging
import getpass
LOGFILE = f"/tmp/mpvsa_{getpass.getuser()}.log"
logging.basicConfig(filename=LOGFILE,
                    format='%(asctime)s %(message)s',
                    filemode='a')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def mpv_with_effects():
    CMD = ' --lavfi-complex="[aid1]showcqt=s=640x480:bar_v=8:sono_v=16:fullhd=1[vo]"'
    CMD2 = ' --lavfi-complex="[aid1]showspectrum=s=640x480:mode=combined:color=intensity:slide=1:scale=log:stop=20000[vo]"'
    return CMD


def combine(primary_language,  secondary_language, ide, merged_path=None):
    """
    this can create two subtitles in the same srt file - for comparisons
    """
    if merged_path is None:
        print("x... no merging")
        return
    # Read files and convert to list
    primary_path =  primary_language
    secondary_path =  secondary_language
    primary_file = open(primary_path, 'r', errors='ignore')
    primary_text = primary_file.read()
    primary_file.close()
    secondary_file = open(secondary_path, 'r', errors='ignore')
    secondary_text = secondary_file.read()
    secondary_file.close()
    subtitle_generator_primary = srt.parse(primary_text)
    subtitles_primary = list(subtitle_generator_primary)
    subtitle_generator_secondary = srt.parse(secondary_text)
    subtitles_secondary = list(subtitle_generator_secondary)

    # Make primary yellow
    for s in subtitles_primary:
        if ide == 1:
            s.content = '<font color="#ffff54">' + s.content + '</font>' # yell
        elif ide == 2:
            s.content = '<font color="#ff5454">' + s.content + '</font>' # RED
        elif ide == 3:
            s.content = '<font color="#ff54ff">' + s.content + '</font>' # magenta
        else:
            s.content = '<font color="#54ffff">' + s.content + '</font>' # cyan

    # Place secondary on top
    for s in subtitles_secondary:
        s.content = '<font color="#77ff77">' + s.content + '</font>'
        s.content = '{\\an8}' + s.content

    # Merge
    print(f"i... merging to {merged_path}")
    subtitles_merged = subtitles_primary + subtitles_secondary
    subtitles_merged = list(srt.sort_and_reindex(subtitles_merged))

    # Write merged to file
    #merged_path = f"merged_{ide}.srt" # output # "merged.srt"#primary_path.replace(primary_language, 'merged')

    merged_text = srt.compose(subtitles_merged)
    merged_file = open(merged_path, 'w')
    merged_file.write(merged_text)
    merged_file.close()




DEBUG = False
def produce_output_filename(infile, outputname, model_size, language=None):
    """
    same in fawhis and mpvsa
    Generate output SRT filename based on input and parameters
    """
    if DEBUG:
        print(f"> fi {infile}")
        print(f"> di {os.path.dirname(infile)}")
        print(f"> st {os.path.splitext(os.path.dirname(infile))}")
        print(f"> 00 {os.path.splitext(os.path.dirname(infile))[0]}")
        print(f"> --")

    # Extract directory from input file
    dirname = ""
    if os.path.dirname(infile):
        dirname = os.path.splitext(os.path.dirname(infile))[0] + "/"

    if DEBUG:
        print(f"> dn== {dirname}")

    # Handle explicit output name
    if outputname is not None:
        # Use provided output name, override directory if specified
        if os.path.dirname(outputname):
            dirname = ""

        # Ensure .srt extension
        file_name = outputname if outputname.endswith(".srt") else f"{outputname}.srt"
        return dirname + file_name

    # Generate default filename
    basename = os.path.splitext(os.path.basename(infile))[0]

    # Build filename suffix based on language or model_size
    if language:
        file_name = f"{basename}_{language}.srt"
    else:
        file_name = f"{basename}_{model_size}.srt"
    return dirname + file_name






# ================================================================================
#   HELPERS
# --------------------------------------------------------------------------------
def create_audio_chunks(video_file, segment_duration=3600):
    """Create audio chunks from video/audio file"""
    print("i... Making Chunks from AudioFILE ...")
    INFILE = video_file
    FOLDER = os.path.splitext(INFILE)[0]
    EXTENS = os.path.splitext(INFILE)[1]
    print("INFILE:", INFILE)
    print("FOLDER:", FOLDER)
    if not os.path.exists(FOLDER):
        os.mkdir(FOLDER)
    CMD = f'ffmpeg  -hide_banner -i "{INFILE}" -f segment -segment_time {segment_duration} -c copy  "{FOLDER}/chunks_%4d{EXTENS}"'
    print()
    print(CMD)
    print()
    args = shlex.split(CMD)
    print(args)
    sp.run(args)
    print("i... Chunked")
    print(f" run fawhis {FOLDER} -w -m base.en ")
    print(f" run fawhis {FOLDER} -t -l cs ")
    print(f"cat $(ls {FOLDER}/chunks_*_base.en.srt | sort) > joined_file.en.srt")

def run_whisper_transcription(video_file, model_type="english", language=None):
    """
    Run whisper transcription on a file using the new wrapper.

    Args:
        video_file: Path to the video/audio file
        model_type: "english" for English models, "multilingual" for multilingual models
        language: Specific language code (cs, fr, zh, it) or None for auto-detection
    """
    print(f"i... Running whisper transcription on {video_file}")
    logger.info(f"Starting transcription: {video_file} (type: {model_type}, language: {language})")

    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"{fg.red}Error: Missing dependencies: {missing_deps}{fg.default}")
        sys.exit(1)

    try:
        # Choose the appropriate wrapper based on model type or language
        if language:
            # Language-specific transcription
            model_size = "small"
            if not verify_model_availability(model_size):
                print(f"{fg.yellow}Warning: {model_size} not verified, trying base{fg.default}")
                model_size = "base"
            whisper = create_multilingual_whisper(model_size)
            print(f"{fg.cyan}Using language: {language}{fg.default}")

            # Generate output filename with language code
            output_path = produce_output_filename(video_file, None, model_size, language=language)
        elif model_type == "english":
            model_size = "small.en"
            if not verify_model_availability(model_size):
                print(f"{fg.yellow}Warning: {model_size} not verified, trying base.en{fg.default}")
                model_size = "base.en"
            whisper = create_english_whisper(model_size)
            language = "en"
            output_path = produce_output_filename(video_file, None, model_size, language=None)
        else:  # multilingual
            model_size = "small"
            if not verify_model_availability(model_size):
                print(f"{fg.yellow}Warning: {model_size} not verified, trying base{fg.default}")
                model_size = "base"
            whisper = create_multilingual_whisper(model_size)
            language = None  # Auto-detect
            output_path = produce_output_filename(video_file, None, model_size, language=None)

        # Run transcription
        _, _ = whisper.transcribe_file(video_file, language=language, output_path=output_path)
        print(f"{fg.green}Transcription completed successfully!{fg.default}")
        print(f"{fg.green}Output saved to: {output_path}{fg.default}")
        logger.info(f"Transcription completed: {output_path}")

    except Exception as e:
        print(f"{fg.red}Error during transcription: {e}{fg.default}")
        logger.error(f"Transcription failed: {e}")
        sys.exit(1)

def merge_subtitles(subtitle_list):
    """Helper function to merge subtitles"""
    subtitle = [x for x in subtitle_list if x.find("merged") < 0]
    if len(subtitle) > 1:
        for i in range(1, len(subtitle)):
            merged_path = produce_output_filename( subtitle[i], None, model_size=f"merged{i}")
            combine(subtitle[0], subtitle[i], i, merged_path=merged_path)
        print("i... MERGED")
        return True
    return False

# ================================================================================
#   constructs the CMD
# --------------------------------------------------------------------------------
def mpvsub( subtitles, audios, video_file, effects=""):
    opt = ""
    optau = ""
    if subtitles is not None and len(subtitles) > 0:
        for i in subtitles:
            opt = f"{opt} --sub-file={i} "
    if audios is not None and len(audios) > 0:
        for i in audios:
            optau = f"{optau} --audio-file={i} "
    # *********** RUN THIS ***************
    CMD = f"mpv  {effects}  --no-sub-auto {opt} {optau} {video_file}"
    return CMD
    # mpv "${sub_options[@]}" --no-sub-auto  --sid=1 "$video_file"





# ================================================================================
# RUNS
# --------------------------------------------------------------------------------
def runcmd(CMD):
    #CMD = f"mpv {general_filename} --sub-file={another_filename}"
    args = shlex.split(CMD)
    sp.run(args)

def confirm_selection(audio, subtitle):
    print()

    # Print suggested audio files
    print(f"Suggested    Audio:", end="")
    if audio:
        print()
        for i, file in enumerate(audio):
            if i == 0:
                print(f"                    {file}")
            else:
                print(f"                    {file}")
    else:
        print(" (none found)")

    # Print suggested subtitle files
    print(f"Suggested Subtitle(s):", end="")
    if subtitle:
        print()
        for i, file in enumerate(subtitle):
            if i == 0:
                print(f"                    {file}")
            else:
                print(f"                    {file}")
    else:
        print(" (none found)")

    print()
    # Display organized menu options
    print(f"{fg.cyan}╔═════════════════════════════════════════════════════════════════╗{fg.default}")
    print(f"{fg.cyan}║                MPVSA OPTIONS                                    ║{fg.default}")
    print(f"{fg.cyan}╠═════════════════════════════════════════════════════════════════╣{fg.default}")
    print(f"{fg.cyan}║  Playback:   {fg.white}Enter{fg.cyan}    - Play with suggested files               ║{fg.default}")
    print(f"{fg.cyan}║  Merge:      {fg.white}m{fg.cyan}      - Merge multiple subtitles                  ║{fg.default}")
    print(f"{fg.cyan}║  Chunks:     {fg.white}c{fg.cyan}      - Create audio chunks                       ║{fg.default}")
    print(f"{fg.cyan}║  Whisper:    {fg.white}w{fg.cyan}      - English transcription                     ║{fg.default}")
    print(f"{fg.cyan}║  Multi:      {fg.white}W{fg.cyan}      - Multilingual (auto-detect)                ║{fg.default}")
    print(f"{fg.cyan}╠═════════════════════════════════════════════════════════════════╣{fg.default}")
    print(f"{fg.cyan}║  Language-specific Whisper:                                     ║{fg.default}")
    print(f"{fg.cyan}║  {fg.white}Wcs{fg.cyan} - Czech    {fg.white}Wfr{fg.cyan} - French    {fg.white}Wzh{fg.cyan} - Chinese    {fg.white}Wit{fg.cyan} - Italian  ║{fg.default}")
    print(f"{fg.cyan}╠═════════════════════════════════════════════════════════════════╣{fg.default}")
    print(f"{fg.cyan}║  Quit:       {fg.white}q{fg.cyan}      - Exit program                              ║{fg.default}")
    print(f"{fg.cyan}╚═════════════════════════════════════════════════════════════════╝{fg.default}")
    print()
    choice = input().strip()
    return choice if choice else ""  # Handle empty input as Enter key

def get_dirname(infile):
    dirname = ""
    if os.path.dirname(infile) != "":
        dirname = os.path.splitext(os.path.dirname(infile))[0]
        dirname = f"{dirname}/"
    else:
        dirname = ""
    return dirname

# ================================================================================
#   TIME DISTANCE MODE....... works on dtox or original screencast
# --------------------------------------------------------------------------------

def time_distance(video_filename: str, audio_filename: str) -> float:
    # Extract datetime from video filename
    #video_pattern = r"screencast_from_(\d{2})-(\d{2})-(\d{2})_(\d{2})_(\d{2})_(\d{2})"
    video_pattern = r"screencast[_ ]from[_ ](\d{2})-(\d{2})-(\d{2})[_ ](\d{2})[:_](\d{2})[:_](\d{2})"
    v_match = re.search(video_pattern, video_filename)
    if not v_match:
        raise ValueError("Video filename format incorrect")
    dd, mm, yy, HH, MM, SS = v_match.groups()
    video_dt = dt.datetime.strptime(f"{dd}-{mm}-{yy} {HH}:{MM}:{SS}", "%d-%m-%y %H:%M:%S")

    # Extract datetime from audio filename
    audio_pattern = r".*_(\d{8})_(\d{6})"
    a_match = re.search(audio_pattern, audio_filename)
    if not a_match:
        return 99999999
        #raise ValueError("Audio filename format incorrect")
    date_str, time_str = a_match.groups()
    audio_dt = dt.datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")

    # Return absolute difference in seconds
    return abs((video_dt - audio_dt).total_seconds())



def find_top_matches(video_file, top_n=16, score_cutoff=1, threshold=50.0, time_threshold=60 * 5):
    """
    5 minuts max diff;
    """

    def match_score(name1, name2):
        #print(name1, name2, end=" ")
        score = 0
        for c1, c2 in zip(name1, name2):
            #print(c1, c2, score)
            if c1 == c2:
                score += 1
            else:
                #pass
                break # to end adter 1st failure
        #print(score)
        return score

    def renormalize(scores):
        if not scores:
            return []
        min_score = min(s for s, _ in scores)
        max_score = max(s for s, _ in scores)
        if max_score == min_score:
            return [(100, f) for _, f in scores]
        return [((s - min_score) / (max_score - min_score) * 100, f) for s, f in scores]
    # ---------------------------------------------------------------------------------

    video_base_and_path = os.path.splitext(video_file)[0].lower()
    video_base = os.path.splitext(video_file)[0].lower().split("/")[-1]
    dirname = os.path.dirname(video_file)
    cwd = os.getcwd()
    if dirname != "":
        dirname = f"{dirname}/"
        os.chdir(dirname)
    # I am at video foloder now--------------------

    files = glob.glob("*")

    audio_exts = ('.mp3', '.opus', '.m4a')
    subtitle_ext = '.srt'

    files = [x for x in files if (os.path.splitext(x)[-1].lower() in audio_exts) or (os.path.splitext(x)[-1].lower() == subtitle_ext)]

    audio_matches = []
    subtitle_matches = []

    # --------------  I dont have similarity but Screencast stuff
    if video_base.find("screencast_from_") >= 0:
        print(fg.cyan, "i...   MATCHING BASED ON TIME.... limit 5 minutes .....", fg.default)
        for f in files:
            f_lower = f.lower()
            base = os.path.splitext(f_lower)[0]
            #print(base, end=" " )
            a = time_distance(video_base, base)
            #print(a)
            if f_lower.endswith(audio_exts):
                audio_matches.append( (a, f) )
            elif f_lower.endswith(subtitle_ext):
                subtitle_matches.append( (a, f) )

          #subtitle_matches = []
        audio_matches.sort(key=lambda x: x[0])
        subtitle_matches.sort(key=lambda x: x[0])
        audio_matches = [x for x in audio_matches if x[0] < time_threshold]
        subtitle_matches = [x for x in subtitle_matches if x[0] < time_threshold]
        #sys.exit(0)


    else:
        print(fg.green, "i...   MATCHING BASED ON SIMILARITY....  .....", fg.default)
        for f in files:
            f_lower = f.lower()
            base = os.path.splitext(f_lower)[0]
            score = match_score(video_base, base)
            if score >= score_cutoff:
                if f_lower.endswith(audio_exts):
                    audio_matches.append((score, f))
                elif f_lower.endswith(subtitle_ext):
                    subtitle_matches.append((score, f))

        audio_matches = renormalize(audio_matches)
        subtitle_matches = renormalize(subtitle_matches)
        audio_matches = [x for x in audio_matches if x[0] > threshold]
        subtitle_matches = [x for x in subtitle_matches if x[0] > threshold]

        audio_matches.sort(key=lambda x: x[0], reverse=True)
        subtitle_matches.sort(key=lambda x: x[0], reverse=True)


    if dirname != "":
        audio_matches = [(x[0], f"{dirname}{x[1]}") for x in audio_matches]
        subtitle_matches = [ (x[0], os.path.join(dirname, x[1])) for x in subtitle_matches]
        os.chdir(cwd)


    top_audio = [f for _, f in audio_matches[:top_n]]
    top_subtitle = [f for _, f in subtitle_matches[:top_n]]

    return top_audio, top_subtitle



# @click.option('--sox_spectrogram', '-x', is_flag=True, help='use sox and create spectrogram')
# @click.option('--spectrum_mp4', '-s', is_flag=True, help="create waterfall spectrum when video_file is audio")

@click.command()
@click.argument('video_file', default=None)
@click.option('--merge', '-m', is_flag=True, help="merge 2 subtitles together")
@click.option('--convert-all-subfolders', '-c', is_flag=True, help='Run embedded bash script')
@click.option('--prepend_silence', '-p', default=0, help='prepend x seconds of silence to opus using ffmppeg')
@click.option('--whisper', '-w', is_flag=True, help='run English whisper transcription on the file')
@click.option('--whisper-multi', '-W', is_flag=True, help='run multilingual whisper transcription on the file')
def main( video_file,  merge, convert_all_subfolders, prepend_silence, whisper, whisper_multi ):
    """
    run mpv with audio+subtitles OR join srt subtitles OR create audio transcription
    """

    is_there_new_version(package="jusflaudio", printit=True, printall=True)

    # Log mpvsa startup
    if video_file:
        logger.info(f"MPVSA started with file: {video_file}")
    else:
        logger.info("MPVSA started without file (showing help)")

    if video_file == "conv":
        print("i... Converting all subfolders (same as -c option)")
        convert_all_subfolders = True

    # #
    # if sox_spectrogram   and (video_file.find("opus") >= len(video_file) - 5):
    #     base = os.path.splitext(video_file)[0]
    #     print("i... creating spectrogram to the ", video_file)
    #     bash_script = f"""#!/bin/bash
    #     ffmpeg -y -i {video_file} /tmp/jusaud_output.wav
    #     sox /tmp/jusaud_output.wav -n spectrogram -o {base}.png
    #     """
    #     sp.run(bash_script, shell=True, executable='/bin/bash')
    #     sys.exit(0)


    if convert_all_subfolders:
        bash_script = r"""#!/bin/bash

#for dir in $(ls -d ./*/ 2>/dev/null | sort || echo "./"); do
for dir in $(ls -d ./*/ 2>/dev/null | sort); do :; done; [ -z "$dir" ] && dir="."
    echo "#########################################################################"
    echo "CONVERTING ALL webm,mp3   for opus and srt IN THE FOLDER:  $dir"
    echo "#########################################################################"





    echo -e "\033[33m"  # yellow for webm
    echo "#  VIDEO to INDEXED VIDEO"

  find "$dir" -type f -name "*.webm" | while read -r myfile; do
      echo -e "\033[33m"  # yellow for webm
      output="${myfile%.webm}_converted.webm"
      if [[ "${myfile}" == *_converted* ]]; then
	      echo ... "rekey video ${myfile}"
	  echo "X... Ok... already converted  ${myfile}"
      else
	  if [ ! -f "${output}" ]; then
	      echo ... "rekey video ${myfile}"
	      ffmpeg -hide_banner -i "${myfile}" -c:v libvpx -crf 10 -b:v 1M -keyint_min 1 -g 30 -c:a libvorbis -threads 16 "${output}" </dev/null
	      echo ... "DONE rekey video ${myfile}"
	      sleep 2
	  fi
      fi
  done
  echo -e "\033[0m"




  echo -e "\033[32m"  # green for mp3
   echo "#  MP3 to OPUS "

  find "$dir" -type f \( -name "*.mp3" -o -name "*.m4a" \) | while read -r myfile; do
      echo -e "\033[32m"  # green for mp3
      if [[ "${myfile}" == *m4a* ]]; then
	  output="${myfile%.m4a}_converted.opus"
      fi
      if [[ "${myfile}" == *mp3* ]]; then
	  output="${myfile%.mp3}_converted.opus"
      fi
      if [ ! -f "${output}" ]; then
	  echo ... opusify "${myfile}"
	  ffmpeg  -hide_banner  -i "${myfile}" -c:a libopus -b:a 16k -af "acompressor=threshold=-10dB:ratio=2:attack=50:release=200" -threads 16  "${output}" </dev/null
	  echo ... DONE opusify "${myfile}"
	  sleep 2
      fi
  done
  echo -e "\033[0m"




  echo -e "\033[36m"  # cyan for opus whisper
  echo "#  OPUS to SRT "


find "$dir" -type f -name "*.opus" | while read -r myfile; do
    echo -e "\033[32m"  # green for mp3
    srt_output="${myfile%.opus}.srt"
    if [ ! -f  "${srt_output}" ]; then
        if [[ "${myfile}" == *czech* ]]; then
	    #fawhis
	    echo ... whisper cs "${myfile}"
	    fawhis "${myfile}" -m medium -l cs -o "${srt_output}"
            #uvx --from openai-whisper whisper --device cpu --language cs --model medium --threads 56 --output_format srt  "${myfile}"
            #uvx --from openai-whisper whisper --device cpu --language cs --model medium --threads 56 --output_format srt --output "${srt_output}" "${myfile}"
	    echo ... DONE whisper cs "${myfile}"
	    sleep 2
        else
echo ... whisper xx "${myfile}"
	    fawhis "${myfile}" -m medium -o "${srt_output}"
            #uvx --from openai-whisper whisper --device cpu --model medium --threads 56 --output_format srt  "${myfile}"
            #uvx --from openai-whisper whisper --device cpu --model medium --threads 56 --output_format srt --output "${srt_output}" "${myfile}"
	    echo ... DONE whisper xx "${myfile}"
	    sleep 2
        fi
    fi
done

# ==========================   clean colors;  finish 1st level DO DONE
echo -e "\033[0m"
        echo ... maybe unexpected done error will appear now ....... .........:
done

        """
        sp.run(bash_script, shell=True, executable='/bin/bash')
        sys.exit(0)

    # Whisper transcription
    if whisper:
        if video_file is None:
            print("X... whisper option requires a video/audio file")
            sys.exit(1)
        run_whisper_transcription(video_file, model_type="english")
        sys.exit(0)

    # Multilingual whisper transcription
    if whisper_multi:
        if video_file is None:
            print("X... whisper-multi option requires a video/audio file")
            sys.exit(1)
        run_whisper_transcription(video_file, model_type="multilingual")
        sys.exit(0)

    # Prepend silence to opus files
    if (prepend_silence > 0) and video_file.find("opus") >= len(video_file) - 5:
        base = os.path.splitext(video_file)[0]
        print("i... prepending silence to the ", video_file)
        bash_script = f"""#!/bin/bash
        ffmpeg -y -f lavfi -i anullsrc=r=48000:cl=mono -t {prepend_silence} /tmp/silence_{prepend_silence}.opus
        ffmpeg -i "concat:/tmp/silence_{prepend_silence}.opus|{video_file}" -c copy {base}_silence.opus
        """
        sp.run(bash_script, shell=True, executable='/bin/bash')
        sys.exit(0)

    #-------------------------------------------------------
    if video_file is None:
        print("""

# NEW: whisper create subtitles (integrated, no shell calls needed)
mpvsa IQt9U5IkBKY_.mp4 -w                 # English transcription with small.en model
mpvsa IQt9U5IkBKY_.mp4 -W                 # Multilingual transcription with small model

# Interactive mode with language-specific whisper:
mpvsa IQt9U5IkBKY_.mp4                   # Then use: w=English, W=Auto, Wcs=Czech, Wfr=French, Wzh=Chinese, Wit=Italian

# OLD: whisper create subtitles (still available)
fawhis IQt9U5IkBKY_.mp4 -w -m base.en

# whisper translate subtitles
fawhis IQt9U5IkBKY_.srt -t -l cs

# this will merge the subttitles and creates merged1 merged2 .... srt files
mpvsa IQt9U5IkBKY_.mp4 -m

# imprint subtit to video IMPRINT_SUBTIT.LUA
#  GENERATE THIS FROM mpv (mpvsa)
#         -select the correct subtitle and do 'k'
#
ffmpeg -i  IQt9U5IkBKY_.mp4 -vf "subtitles=IQt9U5IkBKY_base.en_cs_merged2.srt"  b_20250712.mp4

        """)
        print("X... give me video file and we will see")
        sys.exit(0)



    #fcomment = 6
    #fname = os.path.splitext(video_file)[0]
    # ---------------------- check if sound -----------------------
    sound_exts = {'.mp3', '.opus', '.m4a', '.wav', '.flac', '.aac', '.mka'}
    exists = os.path.isfile(video_file)
    ext = os.path.splitext(video_file)[1].lower()
    is_sound = ext in sound_exts


    if is_sound:
        print(f"i... {fg.orange}SOUND ONLY{fg.default}  {video_file}\n")
    else:
        print(f"i... {fg.lightgreen}VIDEO + SOUND{fg.default}  {video_file}\n")



    # if is_sound and spectrum_mp4:
    #     base, _ = os.path.splitext(video_file)
    #     mp4_file = base + '.mp4'
    #     if os.path.isfile(mp4_file):
    #         print(f"X... file {mp4_file} already exists. ")
    #         sys.exit(1)
    #     CMD = f"time ffmpeg  -hide_banner  -i {video_file} -filter_complex showspectrum=mode=combined:scale=sqrt:color=plasma:slide=1:fscale=log:s=300x180:win_func=gauss -y -acodec copy {mp4_file}"
    #     print(CMD)
    #     runcmd(CMD)
    #     sys.exit(0)


    print("i... LOOKING FOR MATCHES....")
    logger.info(f"Looking for matches for: {video_file}")
    audio, subtitle = find_top_matches(video_file)#best_match(video_file)

    if not audio and not subtitle:
        print(f"{fg.red}Warning: No matching audio or subtitle files found.{fg.default}")
    elif not audio:
        print(f"{fg.yellow}Warning: No matching audio files found.{fg.default}")
    elif not subtitle:
        print(f"{fg.yellow}Warning: No matching subtitle files found.{fg.default}")
    else:
        print(f"{fg.green}Found {len(audio)} audio and {len(subtitle)} subtitle files{fg.default}")

    #print("Audio:", audio)
    #print("Subtitle:", subtitle)
    res = confirm_selection(audio, subtitle)
    if  res == "": # --------------------------------------- PLAYING ENTER
        print("i... Confirmed. Playing...")


    elif res == "m": # --------------------------------------- MERGING  m
        print("i... Merging subtitles...")
        if merge_subtitles(subtitle):
            sys.exit(0)

    elif res == "c": # --------------------------------------- CHUNKS  c
        create_audio_chunks(video_file)
        sys.exit(0)

    elif res == "w": # --------------------------------------- WHISPER  w (English)
        print("i... Running English whisper transcription...")
        run_whisper_transcription(video_file, model_type="english")
        sys.exit(0)

    elif res == "W": # --------------------------------------- WHISPER  W (Multilingual)
        print("i... Running multilingual whisper transcription...")
        run_whisper_transcription(video_file, model_type="multilingual")
        sys.exit(0)

    elif res == "Wcs": # --------------------------------------- WHISPER  Wcs (Czech)
        print("i... Running Czech whisper transcription...")
        run_whisper_transcription(video_file, language="cs")
        sys.exit(0)

    elif res == "Wfr": # --------------------------------------- WHISPER  Wfr (French)
        print("i... Running French whisper transcription...")
        run_whisper_transcription(video_file, language="fr")
        sys.exit(0)

    elif res == "Wzh": # --------------------------------------- WHISPER  Wzh (Chinese)
        print("i... Running Chinese whisper transcription...")
        run_whisper_transcription(video_file, language="zh")
        sys.exit(0)

    elif res == "Wit": # --------------------------------------- WHISPER  Wit (Italian)
        print("i... Running Italian whisper transcription...")
        run_whisper_transcription(video_file, language="it")
        sys.exit(0)

    elif res == "q": # --------------------------------------- QUIT  q
        print("i... Quitting...")
        sys.exit(0)

    else:#-------------------------------------------------------- ELSE CANCEL
        print(f"{fg.red}✖ Invalid option: '{res}'{fg.default}")
        print(f"{fg.yellow}Valid options: Enter=play, m=merge, c=chunks, w=English, W=Multilingual, Wcs=Czech, Wfr=French, Wzh=Chinese, Wit=Italian, q=quit{fg.default}")
        sys.exit(0)

    # merging
    if merge:
        if merge_subtitles(subtitle):
            sys.exit(0)

    # ************** RUN MPV *************
    if is_sound:
        cmdeff = mpv_with_effects()
        cmd = mpvsub(subtitle, audio, video_file, effects=cmdeff)
    else:
        cmd = mpvsub(subtitle, audio, video_file)
    print(cmd)
    logger.info(f"Running MPV command: {cmd}")
    runcmd(cmd) # RUN HERE

# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
