import shlex
import subprocess
from typing import List, Sequence, Optional
import os


def build_smartctl_command(device: str) -> List[str]:
    """Construct the smartctl command safely."""
    return shlex.split(f"sudo smartctl -l error {shlex.quote(device)}")


def run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Execute a command and return the completed process."""
    return subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        check=False,
    )


def validate_audio_file(file_path: str) -> bool:
    """
    Validate if a file exists and has a supported audio/video format.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        True if file exists and is supported, False otherwise
    """
    if not os.path.exists(file_path):
        return False
        
    # Supported audio/video extensions
    supported_exts = {
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',  # Video
        '.mp3', '.wav', '.flac', '.aac', '.m4a', '.opus', '.ogg'  # Audio
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    return ext in supported_exts


def get_media_duration(file_path: str) -> Optional[float]:
    """
    Get the duration of a media file using ffmpeg.
    
    Args:
        file_path: Path to the media file
        
    Returns:
        Duration in seconds, or None if failed
    """
    try:
        cmd = [
            'ffmpeg', '-i', file_path, 
            '-f', 'null', '-'
        ]
        result = run_command(cmd)
        
        # Parse duration from ffmpeg output
        for line in result.stderr.split('\n'):
            if 'Duration:' in line:
                duration_str = line.split('Duration:')[1].split(',')[0].strip()
                # Parse HH:MM:SS.ms format
                h, m, s = duration_str.split(':')
                seconds = int(h) * 3600 + int(m) * 60 + float(s)
                return seconds
    except Exception:
        pass
        
    return None
