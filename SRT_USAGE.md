# SRT Subtitle Support in KokoroDoki

## Overview

KokoroDoki now supports generating timed audio from SRT subtitle files. This feature allows you to create perfectly synchronized audio content that matches subtitle timestamps. SRT files are automatically detected based on the `.srt` file extension.

## Usage

### Basic Usage
```bash
# Generate timed audio from SRT file (auto-detected)
kokorodoki -f subtitles.srt -o synchronized_audio.wav
```

### With Custom Voice and Language
```bash
# American English with heart voice
kokorodoki -f subtitles.srt -l a -v af_heart -o output.wav

# British English with lily voice
kokorodoki -f subtitles.srt -l b -v bf_lily -o british_audio.wav
```

## SRT File Format

SRT files should follow the standard format:
```
1
00:00:00,000 --> 00:00:03,000
First subtitle text goes here.

2
00:00:04,000 --> 00:00:07,500
Second subtitle with multiple lines
can span across several lines.

3
00:00:08,500 --> 00:00:12,000
Third subtitle entry.
```

## Features

- **Automatic Detection**: SRT files are automatically detected by `.srt` extension
- **Perfect Timing**: Audio is generated at exact subtitle timestamps
- **Multi-line Support**: Subtitles spanning multiple lines are handled correctly
- **Flexible Duration**: Adapts to different subtitle timing patterns
- **Voice Options**: Use any available voice and language combination

## Example Files

- `test_subtitle.srt` - Simple 5-entry example
- `example_subtitles.srt` - More comprehensive 8-entry demonstration

## Technical Details

- Generated audio maintains silence between subtitle entries
- Long subtitles are automatically split into sentences for better processing
- Audio duration matches the longest subtitle timestamp
- Stereo output format is used for compatibility

## Limitations

- SRT files must use the standard format (index, timestamp, text)
- The `--all` flag is not supported with SRT files (use single voice)
- Output format is always WAV
- Files must have `.srt` extension to be detected as SRT files

## Troubleshooting

If you encounter issues:
1. Verify your SRT file follows the standard format
2. Check that timestamps are in HH:MM:SS,mmm format
3. Ensure the SRT file is UTF-8 encoded
4. Make sure each entry has an index, timestamp, and text
