#!/bin/bash

# Script to prepare video re-encoding commands for Chromecast v3 compatibility
# Uses ffmpeg for efficient stream copying and selective encoding
# Compatible codecs: video=h264, audio=aac/mp3/opus

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
MAGENTA='\033[1;35m'
NC='\033[0m' # No Color

# Output file for commands
OUTPUT_FILE="recode_commands.sh"

# Global option: force opus encoding for all audio
FORCE_OPUS=0

# Dry run mode: show table of video info without generating commands
DRY_RUN=0

CRF=33
SPEED="fast"

# Default bitrate for video when detection fails
DEFAULT_VIDEO_BPS=1950000

# Maximum bitrate for video encoding (cap at 2000 kbps)
MAXBITRATE=2000100

# Check if required tools are installed
check_tools() {
    echo "Checking for required tools..."
    local missing_tools=0

    if ! command -v ffmpeg &> /dev/null; then
        echo -e "${RED}ERROR: ffmpeg is not installed${NC}"
        missing_tools=1
    else
        echo -e "${GREEN}✓ ffmpeg found${NC}"
    fi

    if ! command -v ffprobe &> /dev/null; then
        echo -e "${RED}ERROR: ffprobe is not installed${NC}"
        missing_tools=1
    else
        echo -e "${GREEN}✓ ffprobe found${NC}"
    fi

    if [ $missing_tools -eq 1 ]; then
        echo -e "${RED}Please install missing tools before running this script${NC}"
        exit 1
    fi
}

# Find all video files
find_videos() {
    local search_dir="${1:-.}"
    echo "Searching for video files in: $search_dir" >&2
    find -L "$search_dir" -type f  -size +0c \( -iname "*.avi" -o -iname "*.mp4" -o -iname "*.mkv" \) 2>/dev/null
}

# Fallback function to calculate bitrate from ffmpeg stream copy
# Returns bitrate in bits per second
get_bitrate_fallback() {
    local video_file="$1"
    local stream_type="$2"  # "video" or "audio"

    # Check if audio stream exists first (for audio bitrate requests)
    if [ "$stream_type" = "audio" ]; then
        local audio_stream_count=$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$video_file" 2>/dev/null | wc -l)
        if [ "$audio_stream_count" -eq 0 ]; then
            echo "NONE"
            return
        fi
    fi

    # Get duration first
    local duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null)
    if [ -z "$duration" ] || [ "$duration" = "0" ] || [ "$duration" = "N/A" ]; then
        echo ""
        return
    fi

    # Run ffmpeg to get stream size in kB
    local size_kb=""
    if [ "$stream_type" = "video" ]; then
        size_kb=$(ffmpeg -nostdin -i "$video_file" -map 0:v:0 -c copy -f null - 2>&1 | sed -n 's/.*video:\([0-9]\+\)kB.*/\1/p')
    else
        size_kb=$(ffmpeg -nostdin -i "$video_file" -map 0:a:0 -c copy -f null - 2>&1 | sed -n 's/.*audio:\([0-9]\+\)kB.*/\1/p')
    fi

    # If we got a size, calculate bitrate
    # bitrate (bps) = (size_kB * 1024 bytes/kB * 8 bits/byte) / duration_seconds
    if [ -n "$size_kb" ] && [ "$size_kb" -gt 0 ]; then
        local bitrate=$(awk "BEGIN {printf \"%.0f\", ($size_kb * 1024 * 8) / $duration}")
        echo "$bitrate"
    else
        echo ""
    fi
}

# Get video information using ffprobe
get_video_info() {
    local video_file="$1"
    local info_type="$2"

    case "$info_type" in
        "vcodec")
            ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null
            ;;
        "acodec")
            local codec=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null)
            if [ -z "$codec" ]; then
                echo "NONE"
            else
                echo "$codec"
            fi
            ;;
        "width")
            ffprobe -v error -select_streams v:0 -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null
            ;;
        "height")
            ffprobe -v error -select_streams v:0 -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null
            ;;
        "vbitrate")
            local bitrate=$(ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null)
            if [ -z "$bitrate" ] || [ "$bitrate" = "N/A" ]; then
                # Fallback to ffmpeg method
                bitrate=$(get_bitrate_fallback "$video_file" "video")
            fi
            echo "$bitrate"
            ;;
        "abitrate")
            local bitrate=$(ffprobe -v error -select_streams a:0 -show_entries stream=bit_rate -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null)
            if [ -z "$bitrate" ] || [ "$bitrate" = "N/A" ]; then
                # Fallback to ffmpeg method
                bitrate=$(get_bitrate_fallback "$video_file" "audio")
            fi
            echo "$bitrate"
            ;;
        "duration")
            ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$video_file" 2>/dev/null
            ;;
    esac
}

# Format duration in seconds to HH:MM:SS
format_duration() {
    local duration="$1"
    if [ -z "$duration" ] || [ "$duration" = "N/A" ]; then
        echo "N/A"
        return
    fi

    # Convert to integer (remove decimals)
    local total_seconds=$(printf "%.0f" "$duration")
    local hours=$((total_seconds / 3600))
    local minutes=$(((total_seconds % 3600) / 60))
    local seconds=$((total_seconds % 60))

    printf "%02d:%02d:%02d" "$hours" "$minutes" "$seconds"
}

# Trim string to max length with ellipsis
# Truncates from the beginning to preserve the filename (end of path)
trim_string() {
    local str="$1"
    local max_len="$2"

    if [ ${#str} -le $max_len ]; then
        echo "$str"
    else
        # Truncate from the beginning, keeping the last (max_len - 3) characters
        local keep_len=$((max_len - 3))
        local str_len=${#str}
        local start_pos=$((str_len - keep_len))
        echo "...${str:$start_pos}"
    fi
}

# Check if codec is in allowed list
is_video_codec_allowed() {
    local codec="$1"
    # Allowed video codec: h264 (also known as avc)
    [[ "$codec" == "h264" ]] || [[ "$codec" == "avc" ]]
}

is_audio_codec_allowed() {
    local codec="$1"
    # Allowed audio codecs: aac, mp3, opus
    [[ "$codec" == "aac" ]] || [[ "$codec" == "mp3" ]] || [[ "$codec" == "opus" ]]
}

# Generate ffmpeg command
generate_ffmpeg_command() {
    local input_file="$1"
    local vcodec="$2"
    local acodec="$3"
    local width="$4"
    local height="$5"
    local vbitrate="$6"
    local abitrate="$7"

    local output_file="${input_file%.*}_chromed2.mkv"

    # Determine video encoding strategy
    local needs_video_encode=0
    local needs_scaling=0
    local scale_filter=""

    # Check if we need to scale
    if [ -n "$width" ] && [ "$width" -gt 1280 ]; then
        needs_scaling=1
        scale_filter="scale=1280:-2"
    fi

    # Determine video codec settings
    if ! is_video_codec_allowed "$vcodec"; then
        # Video needs recoding to h264
        needs_video_encode=1
    elif [ $needs_scaling -eq 1 ]; then
        # Video is h264 but needs scaling, so must encode
        needs_video_encode=1
    elif [ -n "$vbitrate" ] && [ "$vbitrate" != "N/A" ] && [ "$vbitrate" -gt "$MAXBITRATE" ]; then
        # Video bitrate exceeds maximum, needs recoding
        needs_video_encode=1
    fi

    if [ $needs_video_encode -eq 1 ]; then
        # Use 2-pass encoding with original bitrate
        # Default to 2M if bitrate cannot be determined
        local target_vbitrate="$vbitrate"
        if [ -z "$target_vbitrate" ] || [ "$target_vbitrate" = "N/A" ]; then
            target_vbitrate="$DEFAULT_VIDEO_BPS"
        fi

        # Adjust bitrate proportionally if scaling down (do this BEFORE capping)
        if [ $needs_scaling -eq 1 ] && [ -n "$width" ] && [ "$width" -gt 1280 ]; then
            # Calculate bitrate ratio based on width reduction: (new_width / original_width)^2
            # This accounts for the reduction in total pixel count
            local bitrate_ratio=$(awk "BEGIN {printf \"%.4f\", (1280.0 / $width) * (1280.0 / $width)}")
            target_vbitrate=$(awk "BEGIN {printf \"%.0f\", $target_vbitrate * $bitrate_ratio}")
        fi

        # Cap bitrate at maximum if it still exceeds threshold after scaling
        if [ "$target_vbitrate" -gt "$MAXBITRATE" ]; then
            target_vbitrate=="$DEFAULT_VIDEO_BPS" #  "$MAXBITRATE"
        fi

        # Build video filter options
        local vf_opts=""
        if [ $needs_scaling -eq 1 ]; then
            vf_opts="-vf $scale_filter"
        fi

	#
	#       2 PASS VERSION
	#
        # Generate 2-pass command
        local cmd="# \n  toilet -t -f future `basename $input_file`  \n\n # PASS 1 \n"
        cmd="${cmd}ffmpeg -hide_banner -y -i \"$input_file\" $vf_opts -c:v libx264 -b:v $target_vbitrate -pass 1 -an -f null /dev/null && \\\\\n"
        cmd="${cmd}# Pass 2\n# .................  \n "

        # Handle audio encoding for pass 2
        local audio_opts=""
        if [ "$acodec" = "NONE" ]; then
            audio_opts="-an"
        else
            audio_opts="-c:a libopus -ac 2 -ar 48000 -b:a 64k "
        fi

        cmd="${cmd}ffmpeg -hide_banner -i \"$input_file\" $vf_opts -c:v libx264 -b:v $target_vbitrate -pass 2 $audio_opts \"$output_file\""

        echo -e "$cmd"
    else
	#
	#    SINGLE PASS VERSION
	#
        # Video is already h264 and no scaling needed - copy it
        local cmd="ffmpeg  -hide_banner  -i \"$input_file\" -c:v copy"

        # Determine audio encoding strategy
        if [ "$acodec" = "NONE" ]; then
            # No audio stream, skip audio
            cmd="$cmd -an"
        elif [ "$FORCE_OPUS" -eq 1 ]; then
            # Force opus encoding for all audio
            cmd="$cmd -c:a libopus  -ac 2 -ar 48000 -b:a 64k"
        elif is_audio_codec_allowed "$acodec"; then
            # Audio codec is already compatible, copy it
            cmd="$cmd -c:a copy"
        else
            # Audio codec needs recoding, use opus
            cmd="$cmd -c:a libopus   -ac 2 -ar 48000 -b:a 64k"
        fi

        # Add output file
        cmd="$cmd \"$output_file\""

        echo "$cmd"
    fi
}

# Display video info in table format
display_video_table() {
    local search_dir="$1"

    # Get terminal width, default to 80 if not available
    local term_width=$(tput cols 2>/dev/null || echo 80)

    # Fixed column widths
    local W_VCODEC=10
    local W_ACODEC=10
    local W_VRATE=10
    local W_ARATE=10
    local W_LENGTH=10
    local W_SIZE=10

    # Calculate filename column width (terminal width - fixed columns - spaces between columns)
    # Fixed columns total: 60 characters
    # Spaces between 7 columns: 6 characters
    local fixed_width=66
    local W_FILE=$((term_width - fixed_width))

    # Ensure minimum width for filename
    if [ $W_FILE -lt 20 ]; then
        W_FILE=20
    fi

    # Calculate total width for separator line
    local total_width=$((W_VCODEC + W_ACODEC + W_VRATE + W_ARATE + W_LENGTH + W_SIZE + W_FILE + 6))

    # Count total files first for progress display
    local total_files=0
    local current_file=0

    while IFS= read -r video_file; do
        total_files=$((total_files + 1))
    done < <(find_videos "$search_dir" | sort)

    if [ $total_files -eq 0 ]; then
        echo -e "${YELLOW}No video files found in: $search_dir${NC}"
        return
    fi

    echo "Scanning $total_files video files..."
    echo ""

    # Print header
    printf "%-${W_VCODEC}s %-${W_ACODEC}s %${W_VRATE}s %-${W_ARATE}s %-${W_LENGTH}s %${W_SIZE}s %-${W_FILE}s\n" \
        "V-CODEC" "A-CODEC" "V-RATE" "A-RATE" "LENGTH" "SIZE(MB)" "FILENAME"
    printf "%s\n" "$(printf '%.0s-' $(seq 1 $total_width))"

    while IFS= read -r video_file; do
        current_file=$((current_file + 1))
        local progress=$(( (current_file * 100) / total_files ))

        # Show progress on the same line
        printf "\r${YELLOW}Scanning: %d%% (%d/%d)${NC}" "$progress" "$current_file" "$total_files" >&2

        # Get video information
        local vcodec=$(get_video_info "$video_file" "vcodec")
        local acodec=$(get_video_info "$video_file" "acodec")
        local vbitrate=$(get_video_info "$video_file" "vbitrate")
        local abitrate=$(get_video_info "$video_file" "abitrate")
        local duration=$(get_video_info "$video_file" "duration")

        # Format values
        local vcodec_display="${vcodec:-N/A}"
        local acodec_display="${acodec:-N/A}"

        local vrate_display="N/A"
        if [ -n "$vbitrate" ] && [ "$vbitrate" != "N/A" ] && [ "$vbitrate" != "NONE" ]; then
            vrate_display="$(awk "BEGIN {printf \"%.0f\", $vbitrate/1000}")k"
        fi

        local arate_display="N/A"
        if [ "$abitrate" = "NONE" ]; then
            arate_display=""
        elif [ -n "$abitrate" ] && [ "$abitrate" != "N/A" ]; then
            arate_display="$(awk "BEGIN {printf \"%.0f\", $abitrate/1000}")k"
        fi

        local duration_display=$(format_duration "$duration")

        # Get file size in MB
        local file_size=$(stat -c%s "$video_file" 2>/dev/null || echo "0")
        local size_mb=$(awk "BEGIN {printf \"%.0f\", $file_size/1048576}")

        local file_display=$(trim_string "$video_file" $W_FILE)

        # Print row
        printf "%-${W_VCODEC}s %-${W_ACODEC}s %${W_VRATE}s %-${W_ARATE}s %-${W_LENGTH}s %${W_SIZE}s %-${W_FILE}s\n" \
            "$vcodec_display" "$acodec_display" "$vrate_display" "$arate_display" "$duration_display" "$size_mb" "$file_display"

    done < <(find_videos "$search_dir" | sort)

    printf "\n" # Clear the progress line
    echo ""
    echo "Total files: $total_files"
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS] [DIRECTORY]"
    echo ""
    echo "Options:"
    echo "  -D, --dry       Dry run: show table of video codecs, bitrates, and lengths"
    echo "  --force-opus    Force audio encoding to opus for all files (even if audio is already compatible)"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Arguments:"
    echo "  DIRECTORY       Directory to search for videos (default: current directory)"
    echo ""
    echo "Compatible codecs: video=h264, audio=aac/mp3/opus"
}

# Main function
main() {
    local search_dir="."

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -D|--dry)
                DRY_RUN=1
                shift
                ;;
            --force-opus)
                FORCE_OPUS=1
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            -*)
                echo "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                search_dir="$1"
                shift
                ;;
        esac
    done

    echo "================================================"
    echo "Video Recoding Preparation for Chromecast v3"
    echo "================================================"
    echo ""

    # Check tools
    check_tools
    echo ""

    # Handle dry run mode
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "Dry Run Mode: Displaying video information"
        echo ""
        display_video_table "$search_dir"
        exit 0
    fi

    if [ "$FORCE_OPUS" -eq 1 ]; then
        echo -e "${YELLOW}Option: Force opus encoding enabled${NC}"
        echo ""
    fi

    # Initialize output file
    echo "#!/bin/bash" > "$OUTPUT_FILE"
    echo "# Auto-generated ffmpeg re-encoding commands for Chromecast v3 compatibility" >> "$OUTPUT_FILE"
    echo "# Uses stream copying when possible for speed and quality preservation" >> "$OUTPUT_FILE"
    echo "# Generated on: $(date)" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"

    # Count total files first for progress display
    local total_files=0
    local files_need_recoding=0
    local current_file=0

    # Count video files for progress tracking
    while IFS= read -r video_file; do
        total_files=$((total_files + 1))
    done < <(find_videos "$search_dir" | sort)

    if [ $total_files -eq 0 ]; then
        echo -e "${YELLOW}No video files found in: $search_dir${NC}"
        exit 0
    fi

    # Find and process videos
    echo "Analyzing video files..."
    echo ""

    while IFS= read -r video_file; do
        current_file=$((current_file + 1))
        local progress=$(( (current_file * 100) / total_files ))

        # Show progress and current file
        printf "\r${CYAN}[%d%%] Processing %d/%d: %s${NC}" "$progress" "$current_file" "$total_files" "$(trim_string "$video_file" 40)"
        echo "" # Move to next line for detailed output

#        echo -e "${YELLOW}Processing [$current_file/$total_files]: $video_file${NC}"

        # Get video information
        local vcodec=$(get_video_info "$video_file" "vcodec")
        local acodec=$(get_video_info "$video_file" "acodec")
        local width=$(get_video_info "$video_file" "width")
        local height=$(get_video_info "$video_file" "height")
        local vbitrate=$(get_video_info "$video_file" "vbitrate")
        local abitrate=$(get_video_info "$video_file" "abitrate")

        # Format bitrates for display
        local vbitrate_display="N/A"
        local abitrate_display="N/A"
        if [ -n "$vbitrate" ] && [ "$vbitrate" != "N/A" ] && [ "$vbitrate" != "NONE" ]; then
            vbitrate_display="$(awk "BEGIN {printf \"%.2f\", $vbitrate/1000000}")Mbps"
        fi
        if [ "$abitrate" = "NONE" ]; then
            abitrate_display="NONE"
        elif [ -n "$abitrate" ] && [ "$abitrate" != "N/A" ]; then
            abitrate_display="$(awk "BEGIN {printf \"%.0f\", $abitrate/1000}")kbps"
        fi

        echo "  Video codec: $vcodec | Audio codec: $acodec | Resolution: ${width}x${height}"
        echo "  Video bitrate: $vbitrate_display | Audio bitrate: $abitrate_display"

        # Check if recoding is needed
        local needs_recode=0

        if ! is_video_codec_allowed "$vcodec"; then
            echo -e "  ${RED}✗ Video codec needs recoding (not h264)${NC}"
            needs_recode=1
        else
            echo -e "  ${GREEN}✓ Video codec is compatible${NC}"
        fi

        if [ "$acodec" = "NONE" ]; then
            echo -e "  ${YELLOW}⚠ No audio stream present${NC}"
        elif [ "$FORCE_OPUS" -eq 1 ]; then
            echo -e "  ${YELLOW}⚠ Audio will be forced to opus${NC}"
            needs_recode=1
        elif ! is_audio_codec_allowed "$acodec"; then
            echo -e "  ${RED}✗ Audio codec needs recoding (not aac/mp3/opus)${NC}"
            needs_recode=1
        else
            echo -e "  ${GREEN}✓ Audio codec is compatible${NC}"
        fi

        if [ -n "$width" ] && [ "$width" -gt 1280 ]; then
            echo -e "  ${YELLOW}⚠ Resolution will be scaled down to 1280px width${NC}"
            needs_recode=1
        fi

        # Check if video bitrate exceeds maximum
        if [ -n "$vbitrate" ] && [ "$vbitrate" != "N/A" ] && [ "$vbitrate" -gt "$MAXBITRATE" ]; then
            local max_mbps=$(awk "BEGIN {printf \"%.0f\", $MAXBITRATE/1000000}")
            echo -e "  ${YELLOW}⚠ Video bitrate exceeds ${max_mbps}Mbps, will be capped${NC}"
            needs_recode=1
        fi

        # Check if chromecasted version already exists
        local output_file="${video_file%.*}_chromed2.mkv"
        if [ -f "$output_file" ]; then
            echo -e "  ${GREEN}→ Chromed version already exists, skipping${NC}"
            echo ""
            continue
        fi

        # Generate command if needed
        if [ $needs_recode -eq 1 ]; then
            files_need_recoding=$((files_need_recoding + 1))
            local ffmpeg_cmd=$(generate_ffmpeg_command "$video_file" "$vcodec" "$acodec" "$width" "$height" "$vbitrate" "$abitrate")
            echo "" >> "$OUTPUT_FILE"
            echo "# File: $video_file" >> "$OUTPUT_FILE"
            echo "# Original: vcodec=$vcodec, acodec=$acodec, resolution=${width}x${height}" >> "$OUTPUT_FILE"
            echo "# Original bitrates: video=${vbitrate_display}, audio=${abitrate_display}" >> "$OUTPUT_FILE"
            echo -e "$ffmpeg_cmd" >> "$OUTPUT_FILE"
            echo -e "  ${GREEN}→ Command added to $OUTPUT_FILE${NC}"
        else
            echo -e "  ${GREEN}→ No recoding needed${NC}"
        fi

        echo ""

    done < <(find_videos "$search_dir" | sort)

    # Make output file executable
    chmod +x "$OUTPUT_FILE"

    # Summary
    echo ""
    echo "================================================"
    echo "Summary"
    echo "================================================"
    echo "Total video files found: $total_files"
    echo "Files processed: $current_file"
    echo "Files needing recoding: $files_need_recoding"
    echo ""

    if [ $files_need_recoding -gt 0 ]; then
        echo -e "${GREEN}Re-encoding commands have been saved to: $OUTPUT_FILE${NC}"
        echo "To start re-encoding, run: ./$OUTPUT_FILE"
    else
        echo -e "${GREEN}All video files are already compatible with Chromecast v3!${NC}"
    fi
}

# Run main function with optional directory argument
main "$@"
