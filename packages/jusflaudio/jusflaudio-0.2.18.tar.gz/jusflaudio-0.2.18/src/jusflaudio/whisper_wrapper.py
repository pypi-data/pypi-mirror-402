#!/usr/bin/env python3
"""
Clean Python wrapper for faster-whisper functionality.
Replaces the suboptimal shell calls to fawhis.
"""

import os
import logging
import datetime as dt
from typing import Optional, List, Dict, Any
from pathlib import Path

from faster_whisper import WhisperModel
import pysubs2
import autocorrect
from console import fg, bg

from jusflaudio.tool_checker import find_missing_tools
from jusflaudio.shell_calls import run_command


class WhisperWrapper:
    """Clean wrapper for faster-whisper transcription functionality."""
    
    def __init__(self, model_size: str = "base.en", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize the Whisper wrapper.
        
        Args:
            model_size: Whisper model size (tiny.en, base.en, small.en, etc.)
            device: Device to run on (cpu, cuda)
            compute_type: Compute type (int8, float16, etc.)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(f"whisper_wrapper_{id(self)}")
        if not logger.handlers:
            logfile = os.path.expanduser("~/jusflaudio_whisper.log")
            logging.basicConfig(
                filename=logfile,
                format='%(asctime)s %(name)s %(message)s',
                filemode='a'
            )
            logger.setLevel(logging.INFO)
        return logger
        
    def _load_model(self) -> None:
        """Load the Whisper model if not already loaded."""
        if self.model is None:
            print(f"{fg.green}Loading Whisper model: {self.model_size}{fg.default}")
            self.logger.info(f"Loading model {self.model_size} on {self.device}")
            self.model = WhisperModel(
                self.model_size, 
                device=self.device, 
                compute_type=self.compute_type
            )
            
    def _create_output_filename(self, input_file: str, output_name: Optional[str] = None) -> str:
        """
        Generate output SRT filename based on input and parameters.
        Same logic as in fawhis and mpvsa for consistency.
        """
        # Extract directory from input file
        input_path = Path(input_file)
        dirname = input_path.parent
        
        if output_name is not None:
            output_path = Path(output_name)
            if not output_name.endswith('.srt'):
                output_name = f"{output_name}.srt"
            
            # If output_name includes directory, use it as-is
            if output_path.parent != Path('.'):
                return str(output_path)
            else:
                return str(dirname / output_name)
        
        # Generate default filename: {basename}_{model_size}.srt
        basename = input_path.stem
        filename = f"{basename}_{self.model_size}.srt"
        return str(dirname / filename)
        
    def _should_autocorrect(self, language: str) -> bool:
        """Check if autocorrection is supported for the language."""
        return language in ["cs", "en"]
        
    def _get_autocorrect_speller(self, language: str):
        """Get autocorrect speller for supported languages."""
        try:
            return autocorrect.Speller(language)
        except Exception as e:
            self.logger.warning(f"Could not initialize autocorrect for {language}: {e}")
            return None
            
    def transcribe_file(
        self, 
        file_path: str, 
        language: Optional[str] = None, 
        output_path: Optional[str] = None,
        use_autocorrect: bool = True
    ) -> tuple[str, Optional[str]]:
        """
        Transcribe audio/video file to SRT format.
        
        Args:
            file_path: Path to input audio/video file
            language: Language code (en, cs, etc.) or None for auto-detection
            output_path: Custom output path for SRT file
            use_autocorrect: Whether to apply autocorrection if supported
            
        Returns:
            Tuple of (output_srt_path, output_srt_path_autocorrected)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found: {file_path}")
            
        self._load_model()
        
        output_filename = self._create_output_filename(file_path, output_path)
        output_filename_ac = self._create_output_filename(file_path, f"{Path(output_filename).stem}_ac")
        
        print(f"{fg.cyan}Transcribing: {file_path}{fg.default}")
        print(f"{fg.cyan}Output: {output_filename}{fg.default}")
        
        self.logger.info(f"Starting transcription of {file_path} with model {self.model_size}")
        start_time = dt.datetime.now()
        
        try:
            # Transcribe the audio
            if language:
                print(f"{fg.yellow}Using language: {language}{fg.default}")
                segments, info = self.model.transcribe(file_path, beam_size=5, language=language)
            else:
                print(f"{fg.yellow}Auto-detecting language{fg.default}")
                segments, info = self.model.transcribe(file_path, beam_size=5)
                
            detected_language = info.language
            language_probability = info.language_probability
            print(f"{fg.green}Detected language: {detected_language} (probability: {language_probability:.2f}){fg.default}")
            
            # Prepare autocorrect if needed
            speller = None
            if use_autocorrect and self._should_autocorrect(detected_language):
                print(f"{fg.blue}Initializing autocorrect for {detected_language}{fg.default}")
                speller = self._get_autocorrect_speller(detected_language)
                if speller:
                    print(f"{fg.green}Autocorrect enabled for {detected_language}{fg.default}")
                else:
                    print(f"{fg.yellow}Autocorrect failed to initialize for {detected_language}{fg.default}")
            
            # Process segments
            results = []
            results_ac = []
            
            for segment in segments:
                start_time_seg, end_time_seg, text = segment.start, segment.end, segment.text
                
                # Apply autocorrection if available
                corrected_text = text
                if speller:
                    try:
                        corrected_text = speller(text)
                    except Exception as e:
                        self.logger.warning(f"Autocorrect error: {e}")
                        corrected_text = text
                
                print(f"[{start_time_seg:.2f}s -> {end_time_seg:.2f}s] {text}")
                if corrected_text != text and speller:
                    print(f"{fg.darkslategray}[AUTO] {corrected_text}{fg.default}")
                
                # Store results for SRT generation
                segment_dict = {'start': start_time_seg, 'end': end_time_seg, 'text': text}
                segment_dict_ac = {'start': start_time_seg, 'end': end_time_seg, 'text': corrected_text}
                
                results.append(segment_dict)
                results_ac.append(segment_dict_ac)
            
            # Generate SRT files
            subs = pysubs2.load_from_whisper(results)
            subs_ac = pysubs2.load_from_whisper(results_ac)
            
            # Save files
            subs.save(output_filename)
            print(f"{fg.green}Saved: {output_filename}{fg.default}")
            
            # Save autocorrected version if different
            autocorrect_path = None
            if results_ac != results or speller is not None:
                subs_ac.save(output_filename_ac)
                autocorrect_path = output_filename_ac
                print(f"{fg.green}Saved (autocorrected): {output_filename_ac}{fg.default}")
            
            elapsed = dt.datetime.now() - start_time
            print(f"{fg.green}Transcription completed in {elapsed}{fg.default}")
            self.logger.info(f"Completed {file_path} in {elapsed}")
            
            return output_filename, autocorrect_path
            
        except Exception as e:
            error_msg = f"Transcription failed: {e}"
            print(f"{fg.red}{error_msg}{fg.default}")
            self.logger.error(error_msg)
            raise


def create_english_whisper(model_size: str = "small.en") -> WhisperWrapper:
    """Create a WhisperWrapper optimized for English transcription."""
    return WhisperWrapper(model_size=model_size)


def create_multilingual_whisper(model_size: str = "small") -> WhisperWrapper:
    """Create a WhisperWrapper for multilingual transcription."""
    return WhisperWrapper(model_size=model_size)


def check_dependencies() -> List[str]:
    """Check if all required dependencies are available."""
    required_tools = ["ffmpeg"]  # Add other tools if needed
    return find_missing_tools(required_tools)