#!/usr/bin/env python3

#
#   make multiple versions of whisper STT and use mpvsubs.py to play
#
###from fire import Fire
import click
from faster_whisper import WhisperModel
import time
import pysubs2
import os
# importing module
import logging
import datetime as dt
import sys
from console import fg, bg
import autocorrect
#from autocorrect import Speller

from jusflaudio.check_new_version import is_there_new_version

# ================ translate part =================

import argostranslate.package
import argostranslate.translate
import sys
import re
# --------- ooooh  files can be translated too
# .txt, .odt, .odp, .docx, .pptx, .epub, .html, .srt
import argostranslatefiles
from argostranslatefiles import argostranslatefiles
import glob

import subprocess as sp
# uv add argos-translate-files
# OR pip3 install argos-translate-files
#

nested = 0

#
#from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
#https://github.com/snakers4/silero-vad/wiki/Examples-and-Dependencies#examples
#
#
# Create and configure logger

is_there_new_version(package="jusflaudio", printit=True, printall=True)

LOGFILE = os.path.expanduser("~/fwhisp.log")
logging.basicConfig(filename=LOGFILE,
                    format='%(asctime)s %(message)s',
                    filemode='a')
# Creating an object
logger = logging.getLogger()
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.INFO)

"""
https://github.com/SYSTRAN/faster-whisper



2024-08-26 20:09:48,943 Openning FILE speechtest.mp3 with MODEL  tiny.en
2024-08-26 20:09:49,432 Starting FILE speechtest.mp3 with MODEL  tiny.en
2024-08-26 20:09:49,552 Processing audio with duration 01:15.352
2024-08-26 20:09:51,455 Finished FILE speechtest.mp3 with MODEL tiny.en after 0:00:02.022508

2024-08-26 20:09:52,636 Openning FILE speechtest.mp3 with MODEL  base.en
2024-08-26 20:09:53,541 Starting FILE speechtest.mp3 with MODEL  base.en
2024-08-26 20:09:53,657 Processing audio with duration 01:15.352
2024-08-26 20:09:56,501 Finished FILE speechtest.mp3 with MODEL base.en after 0:00:02.959267

2024-08-26 20:09:57,676 Openning FILE speechtest.mp3 with MODEL  small.en
2024-08-26 20:09:58,371 Starting FILE speechtest.mp3 with MODEL  small.en
2024-08-26 20:09:58,489 Processing audio with duration 01:15.352
2024-08-26 20:10:06,467 Finished FILE speechtest.mp3 with MODEL small.en after 0:00:08.095602

2024-08-26 20:10:07,686 Openning FILE speechtest.mp3 with MODEL  medium.en
2024-08-26 20:10:09,583 Starting FILE speechtest.mp3 with MODEL  medium.en
2024-08-26 20:10:09,699 Processing audio with duration 01:15.352
2024-08-26 20:10:31,897 Finished FILE speechtest.mp3 with MODEL medium.en after 0:00:22.314353

2024-08-26 20:10:33,128 Openning FILE speechtest.mp3 with MODEL  distil-medium.en MISSING 45 sec
2024-08-26 20:10:34,222 Starting FILE speechtest.mp3 with MODEL  distil-medium.en
2024-08-26 20:10:34,338 Processing audio with duration 01:15.352
2024-08-26 20:10:43,387 Finished FILE speechtest.mp3 with MODEL distil-medium.en after 0:00:09.164615
"""




DEBUG = False





# ======================================================= translate part


def is_int(n):
    try:
        float_n = float(n)
        int_n = int(float_n)
    except ValueError:
        return False
    else:
        return float_n == int_n


def translate(line, inlang, outlang, silent=True):
    if len(line)==0: return ""
    from_code = inlang #"zh"
    to_code = outlang# "en"

    # Download and install Argos Translate package
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
        )
    )
    argostranslate.package.install_from_path(package_to_install.download())

    # Translate
    translatedText = argostranslate.translate.translate(line, from_code, to_code)
    if not silent: print("outlang:",translatedText)
    # '¡Hola Mundo!'
    return f'{translatedText}'
    #return f'. {line}'

# ================================================================================
#
# --------------------------------------------------------------------------------

def extract_dict(text):
    pattern = r'\[#(\d+)\]\s*([^[]+)'
    matches = re.findall(pattern, text)
    textdict = {int(num): sentence.strip() for num, sentence in matches}
    return textdict

# ================================================================================
#
# --------------------------------------------------------------------------------

def main_translate(srtfile, inlang=None, outlang=None):
    """
    Using argostranslate file -
    """
    print(f"i... translating {srtfile} :: from {inlang} to {outlang}")
    if inlang is None or outlang is None:
        print("H...  languages: en zh (china) cs .....ISO 639 code")
        sys.exit(0)
    n=0


    from_code = inlang #"fr"
    to_code = outlang #"en"
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = list(filter(
        lambda x: x.code == from_code,
        installed_languages))[0]
    to_lang = list(filter(
        lambda x: x.code == to_code,
        installed_languages))[0]
    underlying_translation = from_lang.get_translation(to_lang)
    #
    argostranslatefiles.translate_file(underlying_translation, os.path.abspath(srtfile))

# ================================================================================
#
# --------------------------------------------------------------------------------

def main_translate2( srtfile ,inlang=None, outlang=None):
    """
    Using argostranslate - tested once on chinese
    """
    print(f"i... translating {srtfile} :: from {inlang} to {outlang}")
    if inlang is None or outlang is None:
        print("H...  languages: en zh (china) cs .....ISO 639 code")
        sys.exit(0)
    n=0
    currsub = 0
    if not os.path.exists(srtfile):
        print("H...  srt file not found .....")
        return None

    cummulated_text = [] # try better with complete translate
    time_tags_dict = {} # try better with complete translate
    # --------- open input srt -----------
    with open(srtfile) as f:
        while True:
            n+=1
            line = f.readline()
            #print(n, line.strip(), len(line))
            if line == "": #the end?
                break
            line= line.strip("\n")
            # continue
            # 1
            # 00:00:00,000 --> 00:00:04,640
            # Peace be with you
            # <space>
            #
            if is_int(line): # write this and next
                if int(line)==currsub+1:
                    #
                    print(f"{fg.red}TAG {int(line):4d} >", fg.default, end=" ") # tag+...
                    currsub+=1
                    line2 = f.readline().strip("\n") #timetag and text
                    print(line2.split()[0], end = " ")
                    time_tags_dict[currsub] = line2 #.split()[0] # TIME TAG SAVE
                    #with open( f"{srtfile}.t", "a" ) as wf:
                    #wf.write(f"{line}\n") # Write TIT number
                    cummulated_text.append( f" [#{int(line.strip())}] ") # ADD [#tag]+
                    #wf.write(f"{line2}\n") # Write TIT time
            elif line == "":
                pass# empty line
            else:# prepare for the text itself
                cummulated_text.append( f"{line}")
                print(line ) # just print the line with the text
                #with open( f"{srtfile}.t", "a" ) as wf:
                #    # NOT WRITING ONE BY ONE
                #    #wf.write( translate(line, inlang, outlang) ) # bad that it is translating from the middle
                #    wf.write( "\n" )
            #if n>15:
            #    break
    print("i... translating ... wait ...")
    translated_text = translate(" ".join(cummulated_text), inlang, outlang)
    print("i... translating ... DONE ...")
    translated_text = translated_text.replace("[# ", "[#") # it seems that the translator can insert a space
    translated_text = translated_text.replace("[# ", "[#")
    # --- here I have the text in the one-liner form with [#d+] TAGS
    print("i... reverting to dict ... wait ...")
    ttext_dict = extract_dict(translated_text)
    print("i... reverting to dict ... DONE ...")
    print("i... saving txt version with tags ...  ...")
    with open( f"{srtfile}_{outlang}.txt","w" ) as wf:
            wf.write( translated_text )
            wf.write( "\n" )
    print("i... looping over all lines and writing ... wait ...")
    with open( f"{srtfile}_{outlang}.srt","w" ) as wf:
        for i in time_tags_dict.keys():
            wf.write( f"{i}\n")
            wf.write( f"{time_tags_dict[i]}\n" )
            if i in ttext_dict.keys():
                wf.write( f"{ttext_dict[i]}\n" )
            else:
                print(f"X... missing tag {i} in the translation ...")
                wf.write( f"...\n" )
            wf.write( "\n" )
    print("i... looping over all lines and writing ... DONE ...")



# ======================================================= fawhisper part

# ================================================================================
#
# --------------------------------------------------------------------------------
def produce_output_filename(infile, outputname, model_size):
    """
    same in fawhis and mpvsa ... folder must not have .indide!
    """
    # ================================ OUTPUT ====================
    file_name = "x.srt"
    DEBUG = True
    if DEBUG:
        print(f"> fi {infile}")
        print(f"> di {os.path.dirname(infile)}")
        print(f"> st {os.path.splitext(os.path.dirname(infile))}")
        print(f"> 00 {os.path.splitext(os.path.dirname(infile))[0]}")
        print(f"> --" )
    # --------------------   extract dirname from infile ------------
    dirname = ""
    if os.path.dirname(infile) != "":
        dirname = os.path.splitext(os.path.dirname(infile))[0]
        dirname = f"{dirname}/"
    else:
        dirname = ""
    if DEBUG: print("> dn==", dirname)

    # ----------------------------
    if outputname is not None:
        # ------ cancel my dirname idea if already defined in outputname
        if os.path.dirname(outputname) != "":
            dirname = ""
        if outputname.find(r".srt") > 0:
            file_name = f"{dirname}{outputname}"
        else:
            file_name = f"{dirname}{outputname}.srt"
    else:
        file_name = os.path.splitext(os.path.basename(infile))[0] + f"_{model_size}.srt"
        file_name = f"{dirname}{file_name}"
    if file_name.find("__") > 0:
        file_name = file_name.replace("__", "_")
    return file_name




# ================================================================================
#
# --------------------------------------------------------------------------------
def main_whisper( infile, model_size, language, outputname, current_chunk=0):
    """
    STT for video by whisper. Give me Video-file and model-name (tiny,base...); saves with modelsize in filename; good to test models
    """
    global nested
    nested += 1
    if model_size is None:
        print( """  --models_size OR  -m
        tiny.en, tiny, base.en, base,
        small.en, small,
        medium.en, medium,
        large-v1, large-v2, large-v3,
        distil-large-v2, distil-medium.en, distil-small.en, distil-large-v3
        """)
        sys.exit(1)


    # model_size = "tiny.en" # 0.075 G
    # model_size = "base.en" # 0.144 G
    # model_size = "small.en" # 0.484 G
    # model_size = "distil-medium.en" # 0.789 G
    # model_size = "medium.en" # 1.53 G
    # model_size = "large-v3"  # 3G
    # model_size = "distil-large-v3"  # 3G


    # Run on GPU with FP16
    #model = WhisperModel(model_size, device="cuda", compute_type="float16")
    # or run on GPU with INT8
    # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")

    # or run on CPU with INT8


    ##wav = read_audio( infile) # backend (sox, soundfile, or ffmpeg) required!
    ##speech_timestamps = get_speech_timestamps(wav, model)

    print(f"#...   INPUT:  {infile} ")
    print(f"#...  OUTPUT:  {outputname}")
    if not os.path.exists(infile):
        print("X... file doesnt exist")
        sys.exit(1)


    if os.path.isdir(infile):
        print(f"i... IT IS A FOLDER ...")
        #ext = os.path.splitext(infile)[1]
        #print(ext)
        pabase = os.path.splitext(infile)[1]
        ext = os.path.splitext(infile)[1]

        folder = pabase + "_chunks"
        print("i... ", folder)
        print("i... ", ext)
        pattern = os.path.join(infile, f"chunks_*")
        files = sorted(glob.glob(pattern))
        ii = 0
        for chunkfile in files:
            ii += 1
            print(f"{fg.orange}i...  {os.path.basename(chunkfile)}    {fg.default}")
            main_whisper( chunkfile, model_size, language, outputname, current_chunk=ii)
        sys.exit(0)

    output_file_name = produce_output_filename(infile, outputname, model_size=model_size)
    #print(output_file_name)
    print(f"#... **  OUTPUT:  {output_file_name}")
    if True:
    #???with open(output_file_name, 'w') as f:
        #???f.write("")
        #sys.exit(0)


        print(f"#... **opennin*** MODEL = {model_size} ** logfile ", LOGFILE)
        logger.info(f"Openning FILE {infile} with MODEL  {model_size}")
        model = WhisperModel(model_size, device="cpu", compute_type="int8" ) # fp32 cpu_threads=16, num_workers=16

        timetag = dt.datetime.now()
        logger.info(f"Starting FILE {infile} with MODEL  {model_size} ")


        # *********************** TRANSCRIBE HERE *****************************
        print("#... *** starting transcribe *** ")
        if language is None:
            print(f"#... **no def *** LANGUAGE    ********")
            segments, info = model.transcribe(infile, beam_size=5  )
        else:
            print(f"#... **forcing*** LANGUAGE  = {language} ********")
            segments, info = model.transcribe(infile, beam_size=5, language=language)

        print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

        LANG = info.language
        if LANG in ["cs", "en"]:
            print("#... ********  initializing autocorrect *****")
            spell = autocorrect.Speller( LANG)  # I can tune if english or so...
            print("#... ******* autocorrect initialized *****")

        results= []
        results_ac= []

        # ***************************** OUTPUTS ********************
        print("#... ***** going through  segments *** ")
        chunk = ""
        if nested >= 2:
            chunk = f"{current_chunk:03d}"

        shift_minutes = 60 * (current_chunk - 1)
        # time_format = "%H:%M:%S,%f"
        # shift = dt.timedelta(minutes=shift_minutes)
        # def shift_timestamp(match):
        #     start = datetime.strptime(match.group(1), time_format) + d
        #     end = datetime.strptime(match.group(2), time_format) + shift
        #     return f"{start.strftime(time_format)[:-3]} --> {end.strftime(time_format)[:-3]}"

        for segment in segments:
            SEG_s, SEG_e, SEG_t = segment.start, segment.end, segment.text
            #print(SEG_s, SEG_e)
            if nested >= 2:
                #SEG_s = re.sub(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})",shift_timestamp,SEG_s)
                #SEG_e = re.sub(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})",shift_timestamp,SEG_e)
                SEG_s +=shift_minutes * 60
                SEG_e +=shift_minutes * 60
            SEG_t_ac = "non corrected text"
            if LANG in ["cs", "en"]:
                # spell check running... ???
                SEG_t_ac = spell(SEG_t)
                if SEG_t_ac != SEG_t:
                    # If an error .... Print the original
                    print(f"{chunk}{fg.pink}[{SEG_s:.2f}s -> {SEG_e:.2f}s] {SEG_t} ", fg.default)
                    print(f"{chunk}{fg.darkslategray}[{SEG_s:.2f}s -> {SEG_e:.2f}s] {SEG_t_ac} ", fg.default)
                else:
                    print(f"{chunk}{fg.white}[{SEG_s:.2f}s -> {SEG_e:.2f}s] {SEG_t} ", fg.default)
            else: # no spell check ???
                print(f"{chunk}{fg.white}[{SEG_s:.2f}s -> {SEG_e:.2f}s] {SEG_t} ", fg.default)

            #LINE = f"[{SEG_s:.2f}s -> {SEG_e:.2f}s] {SEG_t_ac}"
            #print(LINE)
            #???f.write(f"{LINE}\n")
            # srt
            segment_dict = {'start':SEG_s,'end':SEG_e,'text':SEG_t}
            segment_dict_ac = {'start':SEG_s,'end':SEG_e,'text':SEG_t_ac}
            results.append(segment_dict)
            results_ac.append(segment_dict_ac)

        logger.info(f"i... Finished FILE {infile} with MODEL {model_size} after {dt.datetime.now()-timetag}")

        subs = pysubs2.load_from_whisper(results)
        subs_ac = pysubs2.load_from_whisper(results_ac)
        #save srt file


    #********************************************************************************
    file_name = produce_output_filename(infile, outputname, model_size=model_size)
    file_name_ac = produce_output_filename(infile, outputname, model_size=f"{model_size}_ac")

    #file_name = os.path.splitext(os.path.basename(infile))[0] + f".srt"
    print("i... saving direct: ", fg.green, file_name, fg.default)
    subs.save( file_name )
    print("i... saving aucorr: ", fg.green, file_name_ac, fg.default)
    subs_ac.save( file_name_ac )
    print("i...  in case of chunks .... ")
    print(f"i...  join  ....     cat $(ls chunks_*_base.en.srt | sort) > joined_file.en.srt")
    print(f"i...  trans ....     fawhis joined_file.en.srt -t -l cs")
    # #save ass file
    # subs.save(file_name+'.ass')



#@click.option('--time_one_chunk', "-t", default=60, help='Chunk of t minutes, default is 15 minutes')
#@click.option('--split_mode', "-s", is_flag=True, help='Split big file into chunks')

@click.command()
@click.argument('infile')
@click.option('--whisper_mode', "-w", is_flag=True, help='WHISPER MODE - not translate')
@click.option('--model_size', "-m", default=None, help='Optional model size like tiny.en small base _medium_')
@click.option('--language', "-l", default=None, help='Optionaly force language like cs')
@click.option('--outputname', "-o", default=None, help='Optionaly overwrite output filename')
@click.option('--translate_mode', "-t", is_flag=True, help='TRANSLATE MODE - not whisper mode')
@click.option('--from_language', "-f", default="en", help='Translate from en or zh or other language')
def main( infile, model_size, language, outputname, translate_mode, whisper_mode, from_language ):
    """
    STT for video by whisper. Give me Video-file and model-name (tiny,base...); saves with modelsize in filename; good to test models
    """
    # split_mode, time_one_chunk
    if translate_mode:
        outlang = language
        inlang = from_language
        print(f"i... translate mode from {inlang} to {outlang}")
        if outlang is None:
            print("X... no target laguage ... -l ... given")
            sys.exit(1)
        main_translate( infile ,inlang, outlang)
    elif whisper_mode:
        print("i... whisper mode")
        main_whisper( infile, model_size, language, outputname)
#     elif split_mode:
#         print("i... split mode")
#         ext = os.path.splitext(infile)[-1]
#         folder = infile.split(ext)[0]
#         folder = folder.rstrip("_")
#         folder = folder.rstrip("_")
#         folder = f"{folder}_chunks"
#         time = time_one_chunk * 60
#         bash_script = f"""
# echo mkdir "{folder}"
# mkdir -p "{folder}"
# ffmpeg -i "{infile}" -f segment -segment_time {time} -c copy  "{folder}/chunks_%4d{ext}"
#         """

#         print(bash_script)
#         sp.run(bash_script, shell=True, executable='/bin/bash')
#         sys.exit(0)


    else:
        print("X... -w or -t mode ... for whisper mode or translate mode")
        print("X...     -w needs a model ... -w -m base.en ... for example")
        print("X...     -t needs a language ... -t -l cs ... for example")


if __name__ == "__main__":
    main()


#!/bin/bash
#filename=$1
#time=${2:-15}
#base="${filename%.*}"
#
#folder="${base}_chunks"
#
#folder="${folder//__/_}"
#folder="${folder//__/_}"
#
#mkdir -p "$folder"
#ffmpeg -i "{$filename}" -f segment -segment_time $((time * 60)) -c copy "$folder/chunks_%4d.${filename##*.}"
