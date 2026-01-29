# Project mpvsa

This all is a part of a braoder package. Focus only on mpvsa.py relevant tasks.

Python wrapper to mpv media player that
 - finds and selects similar-named audio tracks to play
 - finds and selects similar-named subtitles to play
 - allows to call faster whisper to make subtitles (transcription)
 - allows to make audio chunks (for later whisper calls)
 - and, finally, calls mpv with proper parameters.

## Package manager and obligatory modules

PM is uv-astral: this means that
 - all execute calls are like `uv run src/jusflaudio/program.py`
 - packages are added via `uv add package`

 - `click` module is used to handle CLI
 - `console` module is used for colored text output

## Relevant files
 - @src/jusflaudio/mpvsa.py - THE MAIN FILE
 - @src/jusflaudio/fawhis.py -first crude approximation to call faster whisper
 - @src/jusflaudio/shell_calls.py - THIS IS THE MODULE TO CALL SHELL COMMANDS
 - @src/jusflaudio/tool_checker.py - THIS IS THE MODULE TO VERIFY COMMANDS EXISTENCE
 - @src/jusflaudio/check_new_version.py - THIS IS THE MODULE TO VERIFY if this is the last VERSION

## Tasks

THE CONTEXT:
`mpvsa.py`  displays options in interactive mode. The option (w) stands for calling whisper - it is called (via bash) `fawhis`. This is unfortunate, `fawhis` is defined in `@src/jusflaudio/fawhis.py` and it is suboptimal to call shell.

### Task 1 - DONE

  Implement a new and clean variant of `fawhis.py` - `whisper_wrapper.py` that will have the functionality to call faster-whisper .


### Task 2 - DONE

  Use this `whisper_wrapper.py` in `mpvsa.py` instead of `fawhis` bash call - `run_whisper_transcription()`.

### Task 3 - DONE

 The interactive option (w) currently used `base.en` models. Create two options:
  - (w) uses `small.en` by default for english
  - (W) uses `small` by default for other languages

### Taks 4 - DONE

 Extension of the task 3 : interactive options (w) is for english, but the other languages do explicitely:
  - Wcs - for Czech (cs)
  - Wfr - for French
  - Wzh - for Chineese
  - Wit - for Italien

(W) stays for autodetection.

### Task 5 - DONE WITH A DEFECT REMAINING

Aesthetics around interactive menu:

 1. Do not print debug lists SUB and AUD
 2. Align print of "Suggested Audio" and "Suggested Subtitle(s)"
 3. Remove duplicit print and ORGANIZE nicely the menu/the option selections

### Task 6 - DONE BUT THE DEFECT REMAINS

 - the defect from task 5 is : the east side of the menu box is not aligned when the text is present. Widen the box a bit and align - where the text is present

 - The previous fawhis.py version had logging. Create logging to /tmp/mpvsa.log.


### Task 7 - DONE

the defect from task 5 remains : the east side of the menu box is not aligned when the text is present. Widen the box a bit and align - where the text is present


## Further information
 - leave the old `fawhis.py` as is for now, create a new version
 - clean up the code of `mpvsa.py` and suggest improvements
 - treat `shell_calls.py` as a library for calls, that will be extended now and in the future.
 - to help to simplify the code and increase readibility, it is favorable to create other independent python modules
